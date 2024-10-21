import requests
import json
import os

def get_external_ip():
    try:
        response = requests.get('https://httpbin.org/ip')
        response.raise_for_status()  # Raise an error for bad responses
        ip_address = response.json().get('origin')
        return ip_address
    except requests.RequestException as e:
        print(f"Error fetching IP address: {e}")
        return None

def update_ip_address(new_ip):
    # Define the path for the data directory
    data_directory = '../data'

    # Ensure the data directory exists
    os.makedirs(data_directory, exist_ok=True)

    # Define the path for the JSON file
    json_file_path = os.path.join(data_directory, 'get_ip.json')

    # Write the IP address to the JSON file
    data = {"ip_address": new_ip}
    with open(json_file_path, 'w') as json_file:
        json.dump(data, json_file)
    print(f"Updated IP address to: {new_ip} in {json_file_path}")

if __name__ == '__main__':
    ip = get_external_ip()
    if ip:
        update_ip_address(ip)
