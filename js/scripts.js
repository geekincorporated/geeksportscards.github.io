/*!
* Start Bootstrap - Shop Homepage v5.0.6 (https://startbootstrap.com/template/shop-homepage)
* Copyright 2013-2023 Start Bootstrap
* Licensed under MIT (https://github.com/StartBootstrap/startbootstrap-shop-homepage/blob/master/LICENSE)
*/
// This file is intentionally blank
// Use this file to add JavaScript to your project

// Attach event listeners to radio buttons 
document.querySelectorAll('input[name="condition"], input[name="listingType"]').forEach(function (radio) {
radio.addEventListener('change', function () {
if (this.value === "Any") {
// Reset other checkboxes in the same group when "Any" is selected
resetCheckboxes(this.name);
}
search();
});
});

// Function to clear input field
const clearInput = () => {
document.getElementById('searchInput').value = '';
};

// Function to handle Enter key press
const checkEnter = event => {
if (event.key === 'Enter') {
search();
}
};

const resetSearch = () => {
// Clear the search input
document.getElementById('searchInput').value = '';

// Set the "Any" condition radio button to checked
document.getElementById('conditionAny').checked = true;

// Set the "Any" listing type radio button to checked
document.getElementById('listingTypeAny').checked = true;

// Clear all attribute checkboxes
document.querySelectorAll('input[name="attribute"]').forEach(checkbox => checkbox.checked = false);

// Reload the page with default settings
currentPage = 1;
loadPage(currentPage);
};

const resetCheckboxes = (groupName) => {
document.querySelectorAll(`input[name="${groupName}"]`).forEach(function (checkbox) {
if (checkbox.value !== "Any") {
checkbox.checked = false;
}
});
};

document.addEventListener('DOMContentLoaded', (event) => {
document.querySelectorAll('input[name="attribute"]').forEach(checkbox => {
checkbox.addEventListener('change', search);
});

document.querySelectorAll('input[name="condition"]').forEach(radio => {
radio.addEventListener('change', search);
});
});

const search = () => {
const searchTerm = document.getElementById('searchInput').value.toLowerCase();
const selectedCondition = document.querySelector('input[name="condition"]:checked').value;
const selectedListingType = document.querySelector('input[name="listingType"]:checked').value;
const selectedCategory = document.getElementById('searchCategory').value.toLowerCase();
const selectedAttributes = Array.from(document.querySelectorAll('input[name="attribute"]:checked')).map(cb => cb.value.toLowerCase());

const filteredData = allItems.filter(item => {
const nameMatches = item.Title && item.Title.toLowerCase().includes(searchTerm);
const descriptionMatches = item["Item Specifics"] && item["Item Specifics"].some(specific =>
specific.Name.toLowerCase().includes(searchTerm) || specific.Values.some(value => value.toLowerCase().includes(searchTerm))
);
const conditionMatches = selectedCondition === "Any" || (item["Condition Display Name"] && item["Condition Display Name"].toLowerCase() === selectedCondition.toLowerCase());
const listingTypeMatches = selectedListingType === "Any" || (item["Listing Type"] && item["Listing Type"].toLowerCase() === selectedListingType.toLowerCase());
const sportMatches = selectedCategory === 'any' || selectedCategory === 'sport' ||
(item["Item Specifics"] && item["Item Specifics"].some(specific =>
specific.Name.toLowerCase() === 'sport' && specific.Values.some(value => value.toLowerCase() === selectedCategory)
));

const attributeMatches = selectedAttributes.length === 0 || (item["Item Specifics"] && selectedAttributes.every(attr =>
item["Item Specifics"].some(specific => {
if (specific.Name.toLowerCase() === 'attributes') {
// Special handling for UER and ERR
if (attr === 'uer' || attr === 'err') {
    return specific.Values.some(value => value.toLowerCase() === 'uer' || value.toLowerCase() === 'err');
}
return specific.Values.some(value => value.toLowerCase() === attr);
}
return false;
})
));

return (nameMatches || descriptionMatches) && conditionMatches && listingTypeMatches && sportMatches && attributeMatches;
});

totalItems = filteredData.length;
displayItems(filteredData, 0, totalItems);
};


// Function to show filter and perform search
const showFilter = () => {
const resultsfilterContainer = document.getElementById('resultsfilterContainer');
resultsfilterContainer.style.display = 'block';
search();
};

// Show/hide the "Go to Top" button based on scroll position
window.addEventListener('scroll', () => {
const goToTopBtn = document.getElementById("goToTopBtn");
if (document.body.scrollTop > 20 || document.documentElement.scrollTop > 20) {
goToTopBtn.style.display = "block";
} else {
goToTopBtn.style.display = "none";
}
});

// Scroll to the top when the "Go to Top" button is clicked
const goToTop = () => {
document.body.scrollTop = 0;
document.documentElement.scrollTop = 0;
};

// Initialize tooltips
$(document).ready(() => {
$('[data-toggle="tooltip"]').tooltip();
});

var allItems = [];
var currentPage = 1;
var itemsPerPage = 12;
var totalItems = 0;

window.onload = function () {
loadJSON(function (data) {
allItems = Object.values(data);
allItems.sort(function (a, b) {
// First sort by Bids in descending order
const bidsDifference = b.Bids - a.Bids;
if (bidsDifference !== 0) {
return bidsDifference;
}
// If Bids are equal, sort by Watch Count in descending order
const watchCountDifference = b["Watch Count"] - a["Watch Count"];
if (watchCountDifference !== 0) {
return watchCountDifference;
}
// If both Bids and Watch Count are equal, sort by End Time in ascending order
const endTimeA = new Date(a["End Time"]).getTime();
const endTimeB = new Date(b["End Time"]).getTime();
return endTimeA - endTimeB;
});
totalItems = allItems.length;
loadPage(currentPage);
});
};

// Function to load JSON data from a file
function loadJSON(callback) {
var xobj = new XMLHttpRequest();
xobj.overrideMimeType("application/json");
xobj.open('GET', 'data/ebay_listings.json', true);
xobj.onreadystatechange = function () {
if (xobj.readyState == 4 && xobj.status == 200) {
callback(JSON.parse(xobj.responseText).items); // Access items property
}
};
xobj.send(null);
}

// Function to load items for the current page
function loadPage(page) {
var startIndex = (page - 1) * itemsPerPage;
var endIndex = Math.min(startIndex + itemsPerPage, totalItems);
var itemsToShow = allItems.slice(startIndex, endIndex);
displayItems(itemsToShow, startIndex, endIndex);
}

// Function to display items
function displayItems(items, startIndex, endIndex) {
var resultsContainer = document.getElementById('results');
resultsContainer.innerHTML = '';

var totalItemsDiv = document.getElementById('totalItems');
totalItemsDiv.innerHTML = `Showing ${startIndex + 1} - ${endIndex} of ${totalItems} items`;

items.forEach(function (item) {
if (item["Listing Type"] === "FixedPriceItem" || item["Listing Type"] === "Chinese") {
var viewUrl = item["View URL"];
var currentPrice = item["Current Price"].replace('USD', '$').trim();
var pictureUrl = item["Picture URLs"][0];
var condition = item["Condition Display Name"];
var Category = item["Category"];
var categoryID = item["CategoryID"];
var bids = item["Bids"];
var watchers = item["Watch Count"];
var listingtype = item["Listing Type"];
var shippingcost = item["Shipping Cost"];
var bestofferenabled = item["Best Offer Enabled"];
var endtime = item["End Time"];
var card = "";
var year = "";
var set = "";
var cardnumber = "";
var attributes = "";
var authority = "";
var grade = "";
var gradecondition = "";
var team = "";
var sport = "";
var ebayEPN = "?mkcid=1&mkrid=711-53200-19255-0&siteid=0&campid=5339025312&customid=&toolid=10001&mkevt=1";

// Find the value in item specifics

var itemSpecifics = item["Item Specifics"];
for (var i = 0; i < itemSpecifics.length; i++) {
if (itemSpecifics[i].Name === "Sport") {
sport = itemSpecifics[i].Values[0]; // Get the value
break;
}
}

var itemSpecifics = item["Item Specifics"];
for (var i = 0; i < itemSpecifics.length; i++) {
if (itemSpecifics[i].Name === "Player/Athlete") {
playerAthlete = itemSpecifics[i].Values[0]; // Get the value
break;
}
}

var itemSpecifics = item["Item Specifics"];
for (var i = 0; i < itemSpecifics.length; i++) {
if (itemSpecifics[i].Name === "Card") {
card = itemSpecifics[i].Values[0]; // Get the value
break;
}
}

var itemSpecifics = item["Item Specifics"];
for (var i = 0; i < itemSpecifics.length; i++) {
if (itemSpecifics[i].Name === "Set") {
set = itemSpecifics[i].Values[0]; // Get the value
break;
}
}

var itemSpecifics = item["Item Specifics"];
for (var i = 0; i < itemSpecifics.length; i++) {
if (itemSpecifics[i].Name === "Card Number") {
cardnumber = itemSpecifics[i].Values[0]; // Get the value
break;
}
}


var itemSpecifics = item["Item Specifics"];
for (var i = 0; i < itemSpecifics.length; i++) {
if (itemSpecifics[i].Name === "Professional Grader") {
authority = itemSpecifics[i].Values[0]; // Get the value
break;
}
}

var itemSpecifics = item["Item Specifics"];
for (var i = 0; i < itemSpecifics.length; i++) {
if (itemSpecifics[i].Name === "Grade") {
grade = itemSpecifics[i].Values[0]; // Get the value
break;
}
}

var itemSpecifics = item["Item Specifics"];
for (var i = 0; i < itemSpecifics.length; i++) {
if (itemSpecifics[i].Name === "Card Condition") {
gradecondition = itemSpecifics[i].Values[0]; // Get the value
break;
}
}

var itemSpecifics = item["Item Specifics"];
for (var i = 0; i < itemSpecifics.length; i++) {
if (itemSpecifics[i].Name === "Year") {
year = itemSpecifics[i].Values[0]; // Get the value
break;
}
}

var itemSpecifics = item["Item Specifics"];
for (var i = 0; i < itemSpecifics.length; i++) {
if (itemSpecifics[i].Name === "Team") {
team = itemSpecifics[i].Values[0]; // Get the value
break;
}
}

var attributes = [];
for (var i = 0; i < itemSpecifics.length; i++) {
if (itemSpecifics[i].Name === "Attributes") {
attributes = itemSpecifics[i].Values;
break;
}
}

function formatEndTime(endTime, bids = 0, watchers = 0) {
const endDate = new Date(endTime);
const now = new Date();

// Calculate the time difference
const timeDiff = endDate - now;

// Check if the auction has ended
const hasEnded = timeDiff <= 0;
if (hasEnded) {
return "<span style='color: gray; font-size: 12px;'>Auction Ended</span>";
}

// Calculate the time left
const daysLeft = Math.floor(timeDiff / (1000 * 60 * 60 * 24));
const hoursLeft = Math.floor((timeDiff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));

// Format the end date
const daysOfWeek = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const dayOfWeek = daysOfWeek[endDate.getDay()];

let hours = endDate.getHours();
const minutes = String(endDate.getMinutes()).padStart(2, '0');
const ampm = hours >= 12 ? 'PM' : 'AM';
hours = hours % 12;
hours = hours ? hours : 12; // the hour '0' should be '12'

const formattedEndDate = `${hours}:${minutes} ${ampm}`;

// Check if endDate is today
const isToday = endDate.toDateString() === now.toDateString();

// Build the final output
const timeLeftStr = `${daysLeft}d ${hoursLeft}h ( ${isToday ? formattedEndDate : dayOfWeek + ' ' + formattedEndDate} )`;
const bidsStr = bids !== 0 ? `${bids} bid${bids > 1 ? 's' : ''}` : '0 bids';
const watchersStr = watchers !== 0 ? `${watchers} watching` : '0 watching';

const timeLeftStyle = isToday ? 'color: red;' : '';

return `
<span style="font-size: 11px; ${timeLeftStyle}">
${timeLeftStr} · ${bidsStr} · ${watchersStr}
</span>
`;
}

var formattedEndTime = formatEndTime(endtime, bids, watchers);

var resultElement = document.createElement('div');

var productImage = `
<div class="text-center bg-dark" style="height: 310px; padding-bottom: 10px; border-top-right-radius: 5px; border-top-left-radius: 5px; display: flex; align-items: center; justify-content: center;">
<a href="${viewUrl}${ebayEPN}" target="_blank">
<img class="card-img-top" src="${pictureUrl}" alt="${card}" style="max-width: ${condition === 'Graded' ? '172px' : '206px'}; max-height: 276px; padding-top: 10px;" loading="lazy">
<div><span class="badge badge-dark bg-dark" style="width: 206px; border-radius: 0;">${authority} ${grade} ${gradecondition}</span></div>
</a>
</div>`;

var productDetails = `
<div class="card-body w-100 align-items-center justify-content-left text-left" style="height: 150px;">
<span class="fw-bold" style="font-size: 14px; letter-spacing: 0.25px !important; word-spacing: 0.5px; display: inline-block; text-align: left !important;">${playerAthlete}</span>
<br>
<span style="font-size: 12px;">${set} #${cardnumber}</span>
<br>
<span style="font-size: 12px; font-weight: 500;">Team:</span><span style="font-size: 12px;"> ${team}</span>
<br>
${attributes.length > 0 ? `<span style="font-size: 12px; font-weight: 500;">Attributes:</span><span style="font-size: 12px;"> ${attributes.join(' ')}</span> <br>` : ''}
<span style="font-size: 12px; font-weight: 500;">Sport:</span><span style="font-size: 12px;"> ${sport}</span>
</div>
<hr>`;

var productPrice = `
<div class="card-body w-100 d-flex align-items-center justify-content-center" style="height: 60px;">
<div style="width: 100%; text-align: center;">
<dd>${currentPrice}${bestofferenabled === "true" ? `<span style="font-size: 12px; font-weight: 400 !important;"> or Best Offer</span>` : ''}</dd>
<dd>
${listingtype === "FixedPriceItem" && shippingcost === "USD 0.00" ? `<p style="color: green; font-weight: 500; font-size: 12px;">Free Shipping</p>` : ''}
${listingtype === "FixedPriceItem" && shippingcost !== "USD 0.00" ? `<p style="font-weight: 500; font-size: 12px;">Standard Shipping</p>` : ''}
${listingtype !== "FixedPriceItem" && shippingcost === "USD 5.95" ? `<p style="font-weight: 500; font-size: 12px;">Combined Shipping</p>` : ''}
</dd>
</div>
</div>`;

var watchCount = listingtype !== "Chinese" ? `
<div class="card-footer w-100 d-flex align-items-center justify-content-center" style="height: 30px;">
<span style="font-size: 11px;">${watchers} watching</span>
</div>` : '';

var buyNowButton = `
<div class="card-footer w-100 d-flex align-items-center justify-content-center bg-success text-light" style="height: 30px;">
<a href="${viewUrl}${ebayEPN}" target="_blank" style="text-decoration: none; color: inherit; font-size: 12px; font-weight: 700;">${bestofferenabled === "true" ? 'MAKE OFFER / BUY NOW' : 'BUY NOW'}</a>
</div>`;

if (categoryID === "261330") {
resultElement.innerHTML = `
<div class="col mb-5" style="width: 250px;">
<div class="card h-100 d-flex align-items-stretch justify-content-center">
<div class="badge bg-primary text-white position-absolute" style="top: 0.5rem; right: 1.5rem">Complete Set</div>
${productImage}
${productDetails}
${productPrice}
${watchCount}
${buyNowButton}
</div>
</div>`;
} else {
var auctionBadge = listingtype === "Chinese" ? `<div class="badge bg-danger text-light position-absolute" style="top: 0.25rem; right: 0.25rem;">EBAY AUCTION</div>` : '';
var bidButton = listingtype === "Chinese" ? `
<div class="card-footer w-100 d-flex align-items-center justify-content-center bg-primary text-light" style="height: 30px;">
<a href="${viewUrl}${ebayEPN}" target="_blank" style="text-decoration: none; color: inherit; font-size: 12px; font-weight: 700;">PLACE BID</a>
</div>` : '';

resultElement.innerHTML = `
<div class="col mb-5" style="width: 250px;">
<div class="card h-100 d-flex align-items-stretch justify-content-center">
${auctionBadge}
${productImage}
${productDetails}
${productPrice}
${watchCount}
${listingtype === "Chinese" ? `<div class="card-footer w-100 d-flex align-items-center justify-content-between" style="height: 30px;">${formattedEndTime}</div>` : ''}
${listingtype === "Chinese" ? bidButton : buyNowButton}
</div>
</div>`;
}

resultsContainer.appendChild(resultElement);

}
});
}

