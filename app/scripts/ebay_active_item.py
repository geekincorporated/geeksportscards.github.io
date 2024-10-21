import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re
import logging
from datetime import datetime
import json
import os
from itertools import product



logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# NOTE: 
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive"
}

EBAY_SSN_LIST = ["geeksportscards"]
ACTIVE_BASE_URL = "https://www.ebay.com/sch/{cat}/i.html?_ssn={ssn}&Sport={sport}&Graded={graded}&Grade={grade}&Card%2520Condition={condition}&_sop=1&_ipg=240"
ACTIVE_BASE_ITEM_URL = "https://www.ebay.com/itm/"
EBAY_SPORT_LIST = ["Basketball", "Football", "Baseball", "Ice%2520Hockey"]
EBAY_CATEGORY_LIST = [261328, 261329, 261330]
EBAY_GRADED = ["YES", "NO"]
EBAY_GRADE = ["6", "6%252E5", "7", "7%252E5", "8", "8%252E5", "9", "9%252E5", "10"]
EBAY_CARD_CONDITION = ["Near%2520Mint%2520or%2520Better", "Excellent", "Very%2520Good", "Poor"]

REQUEST_DELAY = 2

DATA_DIRECTORY = '../data'
ACTIVE_DATA_FILENAME = 'ebay_active_item.json'

async def fetch_html(session, url, retries=5, backoff_factor=2):
    """Fetch HTML content of the given URL asynchronously with retries."""
    for attempt in range(retries):
        try:
            async with session.get(url, headers=HEADERS) as response:
                if response.status == 200:
                    return await response.text()
                elif response.status == 503:
                    wait_time = backoff_factor ** attempt
                    logger.warning(f"Received 503 Service Unavailable. Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Failed to fetch HTML from {url}. HTTP status: {response.status}")
        except aiohttp.ClientError as e:
            logger.error(f"Client error occurred while fetching {url}: {e}")
        except asyncio.TimeoutError:
            logger.error(f"Timeout occurred while fetching {url}. Retrying...")

    logger.error(f"Exceeded retry limit for {url}.")
    return None

import re

def extract_item_details(details):
    """Extract item ID and item title lookup query from the item details."""
    item_link = details.find_previous('a', class_='s-item__link')
    item_id = None
    item_title = None
    item_lookup_query = None

    if item_link and item_link['href']:
        match = re.search(r'/itm/(\d+)\?', item_link['href'])
        item_id = match.group(1) if match else None

        title_elem = item_link.find('div', class_='s-item__title')
        if title_elem:
            title_span = title_elem.find('span', role='heading')
            if title_span and title_span.text:
                item_title = title_span.text.strip().replace("New Listing", "").strip()

        last_pattern_index = item_title.rfind(' - ')
        if last_pattern_index != -1:
            item_lookup_query = item_title[last_pattern_index + 3:].strip()  
        else:
            item_lookup_query = item_title 

    return item_id, item_title, item_lookup_query

def extract_price_from_span(span):
    """Helper function to extract price from a span."""
    price_text = span.get_text().strip()
    price_match = re.search(r'\$([\d,.]+)', price_text)
    if price_match:
        return float(price_match.group(1).replace(',', ''))
    return None

def extract_prices(item):
    """Extract auction and BIN prices from the item."""
    price_spans = item.find_all('span', class_='s-item__price')
    
    bid_count = extract_bid_count(item)

    best_offer_span = item.find('span', class_='s-item__dynamic s-item__formatBestOfferEnabled')
    best_offer = 1 if best_offer_span else 0

    auction_price, bin_price = None, None
    
    def format_price(price):
        """Helper function to format price as a string with two decimal places."""
        if price is None:
            return "0.00"
        return f"{float(price):.2f}"

    if len(price_spans) == 2:
        auction_price = format_price(extract_price_from_span(price_spans[0]))
        bin_price = format_price(extract_price_from_span(price_spans[1]))
    elif len(price_spans) == 1:
        if bid_count is None:
            bin_price = format_price(extract_price_from_span(price_spans[0]))
        else:
            auction_price = format_price(extract_price_from_span(price_spans[0]))

    return auction_price, bin_price, best_offer

def extract_bid_count(item):
    """Extract bid count from the item."""
    bid_span = item.find('span', class_='s-item__bids s-item__bidCount')
    if bid_span:
        bid_count_match = re.search(r'(\d+) bids', bid_span.get_text())
        if bid_count_match:
            return int(bid_count_match.group(1))
        else:
            return 0  
    return None  

def extract_time_left(item):
    """Extract time left from the item."""
    time_left_span = item.find('span', class_='s-item__time-left')
    if time_left_span:
        return time_left_span.get_text().split(' left')[0]
    return None  

def extract_time_end(item):
    """Extract time end from the item."""
    time_end_span = item.find('span', class_='s-item__time-end')
    if time_end_span:
        return time_end_span.get_text().strip('()')
    return None 

def extract_shipping_cost(details):
    """Extract the shipping cost from item details."""
    shipping_cost = "0.00"
    shipping_elem = details.find('span', class_='s-item__shipping s-item__logisticsCost')
    
    if shipping_elem:
        shipping_text = shipping_elem.get_text(strip=True)
        shipping_cost = shipping_text.replace('Free shipping', '0.00').replace('$', '').replace('+', '').replace('shipping', '').strip()
        shipping_cost = f"{float(shipping_cost):.2f}"

    return shipping_cost

async def extract_img_src(session, item_url, retries=5, backoff_factor=1):
    """Asynchronously fetch image URLs with retries and exponential backoff."""
    img_srcs = []
    attempt = 0
    
    while attempt < retries:
        try:
            async with session.get(item_url, headers=HEADERS, timeout=10) as response:
                if response.status == 200:
                    html_content = await response.text()
                    soup = BeautifulSoup(html_content, 'html.parser')
                    img_tags = soup.select("img")
                    img_srcs = [
                        img['src'] 
                        for img in img_tags 
                        if 'src' in img.attrs and '/images/' in img['src'] and img['src'].endswith('s-l1600.webp')
                    ]
                    return img_srcs
                elif response.status == 429:
                    logger.warning(f"Received 429 Too Many Requests for {item_url}. Retrying after backoff...")
                else:
                    logger.error(f"Failed to fetch images from {item_url}. HTTP status: {response.status}")
                    return img_srcs
        except aiohttp.ClientError as e:
            logger.error(f"Network or client error occurred while fetching {item_url}: {e}")
        except asyncio.TimeoutError:
            logger.error(f"Timeout occurred while fetching {item_url}")
        
        attempt += 1
        backoff_time = (2 ** attempt) * backoff_factor
        logger.info(f"Retrying {item_url} in {backoff_time} seconds (Attempt {attempt}/{retries})...")
        await asyncio.sleep(backoff_time)
    
    logger.error(f"Exceeded retry limit for {item_url}. Skipping...")

    return img_srcs
    
def should_skip_item(item_id, item_title):
    """Check if the item should be skipped based on its item_id."""
    return item_id == '123456' or item_title == "shop on ebay" or item_id is None

async def check_next_page(soup, ssn, sport, category, graded, grade, condition):
    """Check if pagination should stop based on the presence of a disabled next page button or the absence of the pagination nav."""
    pagination_nav = soup.find('nav', role='navigation', class_='pagination')
    if not pagination_nav:
        logger.info(f"seller: {ssn}, category: {category}, sport {sport}, graded: {graded} grade: {grade} condition {condition} Completed")
        return False  

    next_button = pagination_nav.find('button', class_='pagination__next', attrs={'aria-disabled': 'true'})
    if next_button:
        logger.info(f"seller: {ssn}, category: {category}, sport {sport}, graded {graded} grade: {grade} condition: {condition} Completed")
        return False  

    return True  

async def extract_ebay_listing_info(session, soup, ssn, category, sport, graded, grade, condition):
    """Extract item information from eBay HTML using BeautifulSoup."""
    item_list = []

    item_details = soup.find_all('div', class_='s-item__details-section--primary')

    for details in item_details:
        item_id, item_title, item_lookup_query = extract_item_details(details)

        if should_skip_item(item_id, item_title):  
            continue

        shipping_cost = extract_shipping_cost(details)  
        auction_price, bin_price, best_offer = extract_prices(details)  
        auction_time_left = extract_time_left(details)  
        auction_time_end = extract_time_end(details)  
        active_item_url = f"{ACTIVE_BASE_ITEM_URL}{item_id}"

        if auction_price is not None and bin_price is not None:
            ebay_format = ["auction", "bin"]
        elif auction_price is not None and bin_price is None:
            ebay_format = ["auction"]
        elif auction_price is None and bin_price is not None:
            ebay_format = ["bin"]
        else:
            ebay_format = [] 

        if condition == "Near%2520Mint%2520or%2520Better":
            condition = "NM or Better"
        elif condition == "Very%2520Good":
            condition = "Very Good"
        else:
            condition = condition

        if grade == "6%252E5":
            grade = "6.5"
        elif grade == "7%252E5":
            grade = "7.5"
        elif grade == "9%252E5":
            grade = "9.5"
        else:
            grade = grade
            
        item_data = {
            'item_id': item_id,
            'item_title': item_title, 
            'item_lookup_query': item_lookup_query,
            'active_item_url': active_item_url,
            'ebay_ssn': ssn,
            'category': category,  
            'sport': sport,
            'condition': condition,
            'graded': graded,
            'grade': grade,        
            'ebay_format': ebay_format,
            'auction_price': auction_price,
            'auction_time_left': auction_time_left,
            'auction_time_end': auction_time_end,
            'bid_count': extract_bid_count(details),  
            'best_offer_enabled': best_offer,
            'bin_price': bin_price,
            'shipping_cost': shipping_cost,
            'img_srcs': [],  
        }

        item_list.append(item_data)

    img_tasks = [extract_img_src(session, item['active_item_url']) for item in item_list]
    img_results = await asyncio.gather(*img_tasks)

    for item, img_srcs in zip(item_list, img_results):
        item['img_srcs'] = img_srcs

    return item_list  

async def scrape_ssn(session, ssn, category, sport, graded, grade, condition):
    """Scrape items for a specific seller's eBay page with pagination."""
    all_items = []
    
    page_num = 1  
    while True:
        url = ACTIVE_BASE_URL.format(cat=category, ssn=ssn, sport=sport, graded=graded, grade=grade, condition=condition) + f"&_pgn={page_num}"
        logger.info(f"Scraping page {page_num} for seller: {ssn}, category: {category}, sport: {sport}, graded: {graded}, grade: {grade}, conditiion: {condition}")

        html = await fetch_html(session, url)
        if html:
            soup = BeautifulSoup(html, 'html.parser')
            
            page_items = await extract_ebay_listing_info(session, soup, ssn, category, sport, graded, grade, condition)
            all_items.extend(page_items)

            await asyncio.sleep(REQUEST_DELAY)

            if not await check_next_page(soup, ssn, sport, category, graded, grade, condition):
                break

            page_num += 1
        else:
            break

    return all_items

async def scrape_all_ssns():
    """Scrape eBay for all sellers in EBAY_SSN_LIST concurrently."""
    semaphore = asyncio.Semaphore(3)  # Limit the number of concurrent tasks to prevent overwhelming the server

    async with aiohttp.ClientSession() as session:
        async def bounded_scrape(ssn, category, sport, graded, grade, condition):
            async with semaphore:
                return await scrape_ssn(session, ssn, category, sport, graded, grade, condition)

        tasks = []
        for ssn in EBAY_SSN_LIST:
            for category in EBAY_CATEGORY_LIST:
                for sport in EBAY_SPORT_LIST:
                    for graded in EBAY_GRADED:  # Ensure 'graded' is defined in this loop
                        # Case 1: If category == 261329 or category == 261330, skip both EBAY_GRADE and EBAY_CARD_CONDITION
                        if category in [261329, 261330]:
                            grade = None  # No grade looping for these categories
                            condition = None  # No condition looping for these categories
                            tasks.append(bounded_scrape(ssn, category, sport, graded, grade, condition))
                        
                        # Case 2: If graded == "YES", loop through EBAY_GRADE but skip EBAY_CARD_CONDITION
                        elif graded == "YES":
                            for grade in EBAY_GRADE:
                                condition = None  # Skip condition for graded cards
                                tasks.append(bounded_scrape(ssn, category, sport, graded, grade, condition))

                        # Case 3: If graded == "NO" and category == 261328, loop through EBAY_CARD_CONDITION
                        else:
                            grade = None  # Skip grade for ungraded cards
                            if category == 261328:  # Only loop through condition for ungraded cards in category 261328
                                for condition in EBAY_CARD_CONDITION:
                                    tasks.append(bounded_scrape(ssn, category, sport, graded, grade, condition))
                            else:
                                condition = None  # Skip condition for other categories
                                tasks.append(bounded_scrape(ssn, category, sport, graded, grade, condition))

        all_items = await asyncio.gather(*tasks)
    
    return [item for sublist in all_items for item in sublist]


def save_to_json(data):
    """Save data to a JSON file in the specified directory."""
    os.makedirs(DATA_DIRECTORY, exist_ok=True)  

    file_path = os.path.join(DATA_DIRECTORY, ACTIVE_DATA_FILENAME) 

    with open(file_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)
    
    print(f"JSON file generated: {file_path}")

def main():
    """Main function to run the scraping."""
    all_items = asyncio.run(scrape_all_ssns())

    total_records_before = len(all_items)
    print(f"Total number of records fetched before removing duplicates: {total_records_before}")

    unique_items = list({item['item_id']: item for item in all_items}.values())

    total_records_after = len(unique_items)
    print(f"Total number of records after removing duplicates: {total_records_after}")

    save_to_json(unique_items)

if __name__ == "__main__":
    main()
