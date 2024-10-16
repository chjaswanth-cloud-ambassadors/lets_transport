import requests
import time
import random
import json
from bs4 import BeautifulSoup
import os

# Initialize a session
session = requests.Session()

# Define headers to mimic a real browser
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)\
     AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;\
     q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://www.google.com/'
}

session.headers.update(headers)

# Function to get all the city links from the main page
def get_city_links():
    url = "https://transportnagar.in"
    city_links = {}

    try:
        response = session.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Assuming city names and their links are stored within anchor tags <a> inside some container (e.g. div or table)
        city_list = soup.find_all('a', href=True)

        # Loop through the links and construct the city_links dictionary
        for city in city_list:
            city_name = city.text.strip()  # Extract the city name (text within the <a> tag)
            city_url = city['href']        # Extract the URL (href attribute)

            # Only add valid city URLs that start with the base URL
            if city_url.startswith(url):
                city_links[city_name] = city_url

        print(f"Extracted city links: {city_links}")

    except requests.exceptions.HTTPError as err:
        print(f"HTTP error occurred while fetching city links: {err}")
    except Exception as err:
        print(f"Other error occurred while fetching city links: {err}")

    return city_links

# Function to parse the city page and extract the required data
def parse_city_page(soup):
    data = soup.find_all("td", class_="")  # Assuming the data resides in <td> tags
    data_list = []

    for i in range(0, len(data), 11):  # Adjust the step value based on the structure of the <td> tags
        name = data[i].text.strip() if i < len(data) else ''
        address = data[i + 1].text.strip() if i + 1 < len(data) else ''
        contactPerson = data[i + 3].text.strip() if i + 3 < len(data) else ''
        landlineNo = [data[i + 5].text.strip() if i + 5 < len(data) else '', 
                      data[i + 7].text.strip() if i + 7 < len(data) else '']
        email = data[i + 9].text.strip() if i + 9 < len(data) else ''
        location = data[i + 1].text.strip() if i + 1 < len(data) else ''
        
        entry = {
            'name': name,
            'address': address,
            'email': email,
            'website': '',
            'city': '',
            'state': '',
            'landlineNo': landlineNo,
            'contactPerson': [contactPerson],
            'contactNo': [],
            'gstNo': '',
            'companyRegistrationNo': '',
            'truckAvailable': [],
            'services': [],
            'location': [location]
        }
        
        data_list.append(entry)
    
    return data_list

# Function to scrape the page for a specific city with pagination
def scrape_city_page(city_name, city_link):
    page_number = 0  # Start with the first set of entries
    all_city_data = []

    while True:
        url = f"{city_link}/{page_number}"
        try:
            response = session.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # Check for the message indicating no more entries
            no_entries_message = soup.find('p', string="There are no transport entries available")
            if no_entries_message:
                print(f"No more entries found for {city_name}.")
                break

            city_data = parse_city_page(soup)
            if not city_data:
                print(f"No more data on page {page_number} for {city_name}.")
                break

            all_city_data.extend(city_data)

        except requests.exceptions.HTTPError as err:
            print(f"HTTP error occurred while scraping {city_name}: {err}")
            break
        except Exception as err:
            print(f"Other error occurred while scraping {city_name}: {err}")
            break

        page_number += 20
        time.sleep(random.uniform(1, 3))

    return all_city_data

# Function to scrape all cities and save the data to a single JSON file
def scrape_all_cities(city_links):
    all_cities_data = []

    for city_name, city_link in city_links.items():
        print(f"Scraping data for {city_name}...")
        city_data = scrape_city_page(city_name, city_link)
        all_cities_data.extend(city_data)

    # Format the data into the required structure
    json_data = []
    for entry in all_cities_data:
        json_data.append(entry)
    
    final_json = {
        "entity": "Transportnagar",
        "data": json_data
    }

    # Output the JSON (for display or saving to a file)
    json_output = json.dumps(final_json, indent=4)

    # Save the output to a file
    with open('Transportnagar.json', 'w') as f:
        f.write(json_output)

    print("Data for all cities successfully saved to Transportnagar.json.")

if __name__ == "__main__":
    city_links = get_city_links()  # Fetch the dynamic city links
    scrape_all_cities(city_links)  # Scrape data for all cities
