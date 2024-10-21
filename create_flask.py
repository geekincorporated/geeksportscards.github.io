import os
import shutil

# Define the directory structure
directories = {
    'app': ['static/css', 'static/js', 'static/img', 'templates', 'data', 'scripts'],
}

# Files to be moved
files_to_move = {
    'css': 'app/static/css/',
    'js': 'app/static/js/',
    'img': 'app/static/img/',
    'data': 'app/data/',
    'scripts': 'app/scripts/',
    'html': 'app/templates/'
}

# HTML files to move to templates folder
html_files = [
    '401.html', '404.html', '500.html', 'index.html',
    'maint.index.html', 'site_index.html', 'test_feedback.html',
    'test.html', 'test_paypal.html'
]

def create_directory_structure():
    """Create the standard Flask directory structure."""
    for base_dir, sub_dirs in directories.items():
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
        for sub_dir in sub_dirs:
            path = os.path.join(base_dir, sub_dir)
            if not os.path.exists(path):
                os.makedirs(path)
    print("Directory structure created.")

def move_files():
    """Move files to the correct locations."""
    # Move CSS files
    if os.path.exists('css'):
        shutil.move('css', files_to_move['css'])
        print("Moved CSS files to app/static/css/")
    
    # Move JS files
    if os.path.exists('js'):
        shutil.move('js', files_to_move['js'])
        print("Moved JS files to app/static/js/")
    
    # Move Image files
    if os.path.exists('img'):
        shutil.move('img', files_to_move['img'])
        print("Moved Image files to app/static/img/")
    
    # Move Data files
    if os.path.exists('data'):
        shutil.move('data', files_to_move['data'])
        print("Moved Data files to app/data/")
    
    # Move Script files
    if os.path.exists('scripts'):
        shutil.move('scripts', files_to_move['scripts'])
        print("Moved Python scripts to app/scripts/")

    # Move HTML files to templates folder
    for html_file in html_files:
        if os.path.exists(html_file):
            shutil.move(html_file, files_to_move['html'])
            print(f"Moved {html_file} to app/templates/")

def create_app_files():
    """Create app.py, __init__.py, and routes.py files."""
    # Create __init__.py
    init_content = '''from flask import Flask
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    CORS(app)

    from .routes import main_routes
    app.register_blueprint(main_routes)

    return app
'''
    with open('app/__init__.py', 'w') as f:
        f.write(init_content)
    print("Created app/__init__.py")

    # Create routes.py
    routes_content = '''from flask import Blueprint, jsonify, render_template
import json
import os

main_routes = Blueprint('main_routes', __name__)

@main_routes.route('/')
def index():
    return render_template('index.html')

@main_routes.route('/data/active_items')
def active_items():
    with open(os.path.join('app/data', 'ebay_active_item.json')) as f:
        data = json.load(f)
    return jsonify(data)

@main_routes.route('/data/sold_items')
def sold_items():
    with open(os.path.join('app/data', 'ebay_sold_item.json')) as f:
        data = json.load(f)
    return jsonify(data)
'''
    with open('app/routes.py', 'w') as f:
        f.write(routes_content)
    print("Created app/routes.py")

    # Create app.py
    app_py_content = '''from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
'''
    with open('app.py', 'w') as f:
        f.write(app_py_content)
    print("Created app.py")

    # Create run.py
    run_py_content = '''from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
'''
    with open('run.py', 'w') as f:
        f.write(run_py_content)
    print("Created run.py")

def main():
    create_directory_structure()
    move_files()
    create_app_files()
    print("Flask project structure has been successfully created.")

if __name__ == '__main__':
    main()