import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re
import logging
from datetime import datetime
import json
import os

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive"
}

EBAY_SSN_LIST = ["geeksportscards"]
SOLD_BASE_URL = "https://www.ebay.com/sch/i.html?_ssn={ssn}&_sop=13&LH_Sold=1&LH_Complete=1&_ipg=240"
SOLD_BASE_ITEM_URL = "https://www.ebay.com/itm/"
REQUEST_DELAY = 2

DATA_DIRECTORY = '../data'
SOLD_DATA_FILENAME = 'ebay_sold_item.json'

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

def extract_item_details(details):
    """Extract item ID and item title from the item details."""
    item_link = details.find_previous('a', class_='s-item__link')
    item_id = None
    item_title = None

    if item_link and item_link['href']:
        match = re.search(r'/itm/(\d+)\?', item_link['href'])
        item_id = match.group(1) if match else None

        title_elem = item_link.find('div', class_='s-item__title')
        if title_elem:
            title_span = title_elem.find('span', role='heading')
            if title_span and title_span.text:
                item_title = title_span.text.strip()

    return item_id, item_title

def extract_bid_count(details):
    """Extract the bid count from the given element."""
    bid_count = None  # Initialize bid_count to None
    bid_count_span = details.find('span', class_='s-item__bids s-item__bidCount')
    
    if bid_count_span:
        bid_count_text = bid_count_span.get_text(strip=True)
        try:
            bid_count = int(bid_count_text.split(' ')[0])  # Convert bid count to an integer
        except ValueError:
            logger.error(f"Could not convert bid count to integer: {bid_count_text}")
    
    return bid_count

def extract_sold_date(details):
    """Extract and format the sold date from item details."""
    sold_date = "N/A"
    caption_elem = details.find_previous('div', class_='s-item__caption')

    if caption_elem:
        sold_date_elem = caption_elem.find('span', class_='s-item__caption--signal POSITIVE')
        if sold_date_elem:
            sold_date_span = sold_date_elem.find('span')
            if sold_date_span:
                sold_date_text = sold_date_span.get_text(strip=True).replace("Sold ", "")
                try:
                    sold_date_obj = datetime.strptime(sold_date_text.strip(), '%b %d, %Y')
                    sold_date = sold_date_obj.strftime('%Y-%m-%d')
                except ValueError as e:
                    logger.error(f"Error parsing sold date: {e}")

    return sold_date

def extract_sold_price(details):
    """Extract the sold price or listed price (if strikethrough) from item details."""
    sold_price = "0.00"
    price_elements = details.find_all('span', class_='POSITIVE')

    for price_elem in price_elements:
        if 'STRIKETHROUGH' in price_elem.get('class', []):
            listed_price = price_elem.get_text(strip=True).replace('$', '').strip()  
            break

        elif price_elem.get_text(strip=True).startswith('$'):
            sold_price = price_elem.get_text(strip=True).replace('$', '').strip()
            sold_price = f"{float(sold_price):.2f}"
            break

    return sold_price

def extract_best_offer(details):
    """Extract the listed price from best offer elements and return as formatted string with best offer indicator."""
    best_offer = 0
    listed_price = "0.00"  

    best_offer_elements = details.find_all('span', class_='STRIKETHROUGH POSITIVE')

    if best_offer_elements:
        for offer_elem in best_offer_elements:
            listed_price_text = offer_elem.get_text(strip=True).replace('$', '').strip()
            if listed_price_text:
                listed_price = f"{float(listed_price_text):.2f}" 
                best_offer = 1  
                break  

    return listed_price, best_offer  

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
                        if 'src' in img.attrs and '/images/' in img['src'] and img['src'].endswith('s-l140.webp')
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

def should_skip_item(item_id):
    """Check if the item should be skipped based on its item_id."""
    return item_id == '123456' or item_id is None

## Function to check for pagination
async def check_next_page(soup, ssn):
    """Check if pagination should stop based on the presence of a disabled next page button or the absence of the pagination nav."""
    pagination_nav = soup.find('nav', role='navigation', class_='pagination')
    if not pagination_nav:
        logger.info(f"Pagination navigation element not found for SSN '{ssn}' (No more pages).")
        return False  

    next_button = pagination_nav.find('button', class_='pagination__next', attrs={'aria-disabled': 'true'})
    if next_button:
        logger.info(f"Disabled next page button found for SSN '{ssn}' (No more pages).")
        return False  

    logger.info(f"No disabled next page button found for SSN '{ssn}' (More pages available).")
    return True  

async def extract_ebay_listing_info(session, soup, ssn):
    """Extract item information from eBay HTML using BeautifulSoup."""
    item_list = []

    item_details = soup.find_all('div', class_='s-item__details-section--primary')

    for details in item_details:
        item_id, item_title = extract_item_details(details)

        if should_skip_item(item_id):
            continue

        sold_date = extract_sold_date(details)
        sold_price = extract_sold_price(details)
        shipping_cost = extract_shipping_cost(details)
        listed_price, best_offer = extract_best_offer(details)
        bid_count = extract_bid_count(details) 
        
        ebay_format = "auction" if bid_count is not None else "bin"

        sold_item_url = f"{SOLD_BASE_ITEM_URL}{item_id}?nordt=true&orig"

        item_data = {
            'item_id': item_id,
            'item_title': item_title,
            'sold_item_url': sold_item_url,
            'ebay_ssn': ssn,
            'sold_date': sold_date,
            'ebay_format': ebay_format,  
            'sold_price': sold_price,
            'best_offer': best_offer,
            'listed_price': listed_price,
            'shipping_cost': shipping_cost,
            'bid_count': bid_count,  
            'img_srcs': [],  
        }
        item_list.append(item_data)

    img_tasks = [extract_img_src(session, item['sold_item_url']) for item in item_list]
    img_results = await asyncio.gather(*img_tasks)

    for item, img_srcs in zip(item_list, img_results):
        item['img_srcs'] = img_srcs

    return item_list


async def scrape_ssn(session, ssn):
    """Scrape items for a specific seller's eBay page with pagination."""
    page_num = 1
    all_items = []
    
    while True:
        url = f"{SOLD_BASE_URL.format(ssn=ssn)}&_pgn={page_num}"
        logger.info(f"Scraping page {page_num} for seller: {ssn}")

        html = await fetch_html(session, url)
        if html:
            soup = BeautifulSoup(html, 'html.parser')
            
            page_items = await extract_ebay_listing_info(session, soup, ssn)  
            all_items.extend(page_items)

            await asyncio.sleep(REQUEST_DELAY)

            if not await check_next_page(soup, ssn):
                break

            page_num += 1
        else:
            break

    return all_items

async def scrape_all_ssns():
    """Scrape eBay for all sellers in EBAY_SSN_LIST concurrently."""
    semaphore = asyncio.Semaphore(3)  

    async with aiohttp.ClientSession() as session:
        async def bounded_scrape(ssn):
            async with semaphore:
                return await scrape_ssn(session, ssn)

        tasks = [bounded_scrape(ssn) for ssn in EBAY_SSN_LIST]
        all_items = await asyncio.gather(*tasks)
    return [item for sublist in all_items for item in sublist]

def save_to_json(data):
    """Save data to a JSON file in the specified directory."""
    os.makedirs(DATA_DIRECTORY, exist_ok=True)  

    file_path = os.path.join(DATA_DIRECTORY, SOLD_DATA_FILENAME) 

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
