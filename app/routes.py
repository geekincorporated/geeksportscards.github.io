from flask import Blueprint, jsonify, render_template
import json
import os

main_routes = Blueprint('main_routes', __name__)

# Ensure the index page is rendered correctly
@main_routes.route('/')
def index():
    return render_template('index.html')

# Correct the path to the active items JSON file
@main_routes.route('/data/active_items')
def active_items():
    with open(os.path.join('app/data', 'ebay_active_item.json')) as f:
        data = json.load(f)
    return jsonify(data)

# Correct the path to the sold items JSON file
@main_routes.route('/data/sold_items')
def sold_items():
    with open(os.path.join('app/data', 'ebay_sold_item.json')) as f:
        data = json.load(f)
    return jsonify(data)

# Flask2Slack dynamic IP variable
@main_routes.route('/data/get_ip')
def get_ip():  # Renamed function to avoid conflict
    with open(os.path.join('app/data', 'get_ip.json')) as f:
        data = json.load(f)
    return jsonify(data)
