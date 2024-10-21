$(document).ready(function () {
    // Initialize DataTable
    const table = $('#cardsTable').DataTable({
        paging: true,
        info: true,
        pageLength: 10,
        lengthMenu: [10, 25, 50, 100],
        searching: true,
        dom: '<"top"lfi><"table-wrapper"t><"bottom"p><"clear">'
    });

    // Smooth scroll to section 2
    function scrollToSection2() {
        $('html, body').animate({
            scrollTop: $('#section2').offset().top
        }, 800);
    }

    // Collapse the navbar on small screens
    function collapseNavbar() {
        if ($('.navbar-collapse').hasClass('show')) {
            $('.navbar-toggler').click();
        }
    }

    // Collapse navbar when a link is clicked or when clicked outside
    $('.navbar-nav a').on('click', collapseNavbar);
    $(document).on('click', function (event) {
        if (!$(event.target).closest('.navbar').length) {
            collapseNavbar();
        }
    });

    // Show/hide .navbar-brand based on scroll position
    function toggleNavbarBrand() {
        const section1Bottom = $('#section1').offset().top + $('#section1').outerHeight();
        const scrollPos = $(window).scrollTop();

        if (scrollPos >= section1Bottom) {
            $('.navbar-brand').removeClass('invisible');
        } else {
            $('.navbar-brand').addClass('invisible');
        }
    }

    // Call toggleNavbarBrand on page load and when scrolling
    toggleNavbarBrand();
    $(window).on('scroll', toggleNavbarBrand);

    // Format title by splitting at ' - '
    function formatTitle(title) {
        const index = title.lastIndexOf(' - ');
        if (index !== -1) {
            const part1 = title.substring(0, index).trim();
            const part2 = title.substring(index + 3).trim();
            return `${part1}<br>${part2}`;
        }
        return title;
    }

    // Load data from JSON and populate DataTable
    function loadData() {
        fetch('/data/active_items')  // Updated to fetch from the Flask route
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                table.clear();
                data.forEach(item => {
                    const imgSrc = item.img_srcs && item.img_srcs.length > 0 ? item.img_srcs[0] : 'https://via.placeholder.com/150';
                    table.row.add([
                        `<img src="${imgSrc}" class="img-fluid card-img-top" alt="${item.item_title || 'No Title'}" data-bs-toggle="modal" data-bs-target="#imageModal" data-image="${imgSrc}">`,
                        formatTitle(item.item_title || 'No Title'),
                        item.sport || 'N/A',
                        item.graded || 'No',
                        item.grade || 'N/A',
                        `$${item.auction_price || 'N/A'}`,
                        `$${item.bin_price || 'N/A'}`,
                        `$${item.shipping_cost || 'N/A'}`,
                        `${item.auction_time_left || 'N/A'} (Ends: ${item.auction_time_end || 'N/A'})`,
                        `<a href="${item.active_item_url || '#'}" class="btn btn-primary" target="_blank">View on eBay</a>`
                    ]);
                });
                table.draw();
            })
            .catch(error => console.error('Error fetching data:', error));
    }

    // Perform search and scroll to section 2
    function performSearch() {
        const query = $('#customSearch').val();
        if (query) {
            table.search(query).draw();
            scrollToSection2();
        }
    }

    // Bind search button click and Enter key
    $('#searchButton').on('click', performSearch);
    $('#customSearch').on('keyup', function (event) {
        if (event.key === 'Enter') performSearch();
    });

    loadData();
    setInterval(loadData, 60000);

    // Show modal with the clicked image
    $('#imageModal').on('show.bs.modal', function (event) {
        const button = $(event.relatedTarget);
        const imgSrc = button.data('image');
        $('#modalImage').attr('src', imgSrc);
    });
});

// Select the footer and section1
const footer = document.querySelector('.footer');
const section1 = document.querySelector('#section1');

// Create an intersection observer
const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            footer.style.display = 'block'; // Show footer if section1 is in view
        } else {
            footer.style.display = 'none'; // Hide footer if section1 is not in view
        }
    });
}, {
    threshold: 0.1 // Adjust this value to determine how much of section1 needs to be in view
});

// Start observing section1
observer.observe(section1);

// Handle Slack form submission
document.getElementById('slackForm').addEventListener('submit', function(event) {
    event.preventDefault(); // Prevent default form submission

    const formData = new FormData(this);
    const name = formData.get('name');
    const email = formData.get('email');
    const message = formData.get('message');

    // Change this URL to your Flask server's URL
    fetch('http://73.95.22.240:5000/webhook', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name: name, email: email, message: message }), // Include name and email
    })
    .then(response => response.json())
    .then(data => {
        const responseMessage = document.getElementById('responseMessage');
        // Hide the form
        this.style.display = 'none';

        if (data.status === 'success') {
            responseMessage.innerHTML = '<div class="alert alert-success">Message sent successfully!</div>';
        } else {
            responseMessage.innerHTML = '<div class="alert alert-danger">Error: ' + data.message + '</div>';
        }
        responseMessage.style.display = 'block'; // Show the response message
    })
    .catch(error => {
        const responseMessage = document.getElementById('responseMessage');
        responseMessage.innerHTML = '<div class="alert alert-danger">An error occurred: ' + error.message + '</div>';
        responseMessage.style.display = 'block'; // Show the response message
    });
});
