import requests
from bs4 import BeautifulSoup
import json

# URL of the page to scrape
url = "https://www.etransportdirectory.com/index.php"
# Send a GET request to the URL
response = requests.get(url)
# Create a Beautiful Soup object with the page content
soup = BeautifulSoup(response.content, "lxml")

# Find the select element by class
select_element = soup.find('select', class_="form-control input-normal")

# Check if the select element was found
if select_element:
    # Get all the option elements within the select
    options = select_element.find_all("option")

    # Extract the values from the options
    cities = [option.get('value') for option in options if option.get('value')]

# Create a list to hold all city data
all_city_data = []

# Loop through each city
for city in cities:
    # Update the URL for the current city
    url = f"https://www.etransportdirectory.com/browse-categories.php?company_Name=&city={city}&category=Transport+Road&button=Search"
    print(f"Scraping URL: {url}")
    
    # Send a GET request to the webpage
    response = requests.get(url)
    
    # Parse the webpage content using BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find all divs containing the class where the 'a' tags are located
    entries = soup.find_all('div', class_='job-list-content')
    
    # Check if there are any entries for the city
    if len(entries) == 0:
        print(f"No entries found for {city}")
        city_data = {
            'city_name': "",
            'category_name': 'Transport Road',
            'items': [{
                'Company_name': "",
                'More Details from Link 1': "",
                'additional Details from Link 1': "",
                'Link 1': '',
                'Contact Person': [],
                'Mobile No.': [],
                'Services': [],
                'Truck Available': [],
                'address': '',
                'Email': '',
                'WebSite': '',
                'City': '',
                'State': '',
                'GST No.': '',
                'Company Registration No.': '',
                'location':[]
            }]
        }
        all_city_data.append(city_data)
        continue  # Skip to the next city if no entries are found
    
    
    for entry in entries:
        # Find all 'a' tags within the current entry
        a_tags = entry.find_all('a')
        
        # Check if there are at least two 'a' tags
        if len(a_tags) >= 2:
            # Get the first 'a' tag (e.g., company name)
            title_text = a_tags[0].get_text().strip()
            link1 = a_tags[0]['href']
            
            # Create the full URL if the link is relative
            if not link1.startswith("http"):
                link1 = f"https://www.etransportdirectory.com/{link1}"
            
            # Fetch the details from the first link (link1)
            detail_response = requests.get(link1)
            detail_soup = BeautifulSoup(detail_response.text, 'html.parser')
            
            # Extract specific details from the linked page
            detailed_info = detail_soup.find('ul', class_='lest item')
            detailed_info_1 = detail_soup.find('div', class_='about-me item')

            # Extract detailed text
            detailed_text = detailed_info.get_text().strip() if detailed_info else "No details found"
            detailed_text_1 = detailed_info_1.get_text().strip() if detailed_info_1 else "No details found"

            # Store the extracted data in the desired format
            city_data = {
                'city_name': city,
                'category_name': 'Transport Road',
                'items': [{
                    'Company_name': title_text,
                    'More Details from Link 1': detailed_text,
                    'additional Details from Link 1': detailed_text_1,
                    'Link 1': link1
                }]
            }

            # Add this city's data to the main list
            all_city_data.append(city_data)

def clean_string(input_string):
    """Removes unwanted characters from the string."""
    return input_string.replace('\xa0', '').replace(',', '').strip()

def format_scraped_data(scraped_data_list):
    formatted_data = []
    
    for data in all_city_data:
        for item in data['items']:
            more_details = item['More Details from Link 1'].split('\n')
            address = clean_string(more_details[1]) if len(more_details) > 1 else ""
            emails = clean_string(more_details[2]) if len(more_details) > 3 else ""
            email = emails.split(':')[-1].strip() 
            website = clean_string(more_details[3]) if len(more_details) > 5 else ""
            website = website.split(':')[-1].strip()
            city_info = clean_string(more_details[4]).split(',') if len(more_details) > 7 else ["", ""]
            t_city_info=str(city_info)# Get the relevant string

           # Clean and split the string
            city_part = t_city_info.split("Pin Code :")[0].replace("City :", "").strip()
            pin_code_part = t_city_info.split("Pin Code :")[-1].strip()
            state = clean_string(more_details[5]) if len(more_details) > 9 else ""
            state = state.split(':')[-1].strip()
            gst_no = clean_string(more_details[-2]) if len(more_details) > 13 else ""
            company_registration_no = clean_string(more_details[-1]) if len(more_details) > 15 else ""

            additional_details = item['additional Details from Link 1'].split('\n')
            contact_persons = []
            mobile_numbers = []
            trucks_available =[]
            services = []
            landlineNo=[]
            location=[]

            for line in additional_details:
                if 'Contact Person :' in line:
                    contact_persons.append(clean_string(line.replace('Contact Person :', '')))
                if 'Mobile No. :' in line:
                    # Extract mobile numbers by splitting on commas and cleaning
                    mobile_numbers.extend([clean_string(mob) for mob in line.replace('Mobile No. :', '').split(',') if mob.strip()])
                if 'Truck Available :' in line:
                    truck=clean_string(line.replace('Truck Available :', ''))
                    if truck:  # Filter empty strings during collection
                        trucks_available.append(truck)
                    
                if 'Services :' in line:
                    service=clean_string(line.replace('Services :', ''))
                    if service:
                        services.append(service)
            contact_persons = [person for person in contact_persons if person]

            # Ensure that emails are collected correctly
            #email_list = [email for email in emails.split() if email]  # Filter out empty entries
            formatted_entry = {
                'name': clean_string(item['Company_name']) if 'Company_name' in item else None,
                'address': address,
                'email': email,
                'website': website,
                'city': clean_string(data.get('city_name', '')),
                'state': state,
                "landlineNo":landlineNo,
                'contactPerson': contact_persons,  # Store list of contact persons
                'contactNo': mobile_numbers,   
                'gstNo': gst_no,
                'companyRegistrationNo': company_registration_no,    
                'truckAvailable': trucks_available,
                'services': services,
                'location':location    
                
            }
            formatted_data.append(formatted_entry)
    return formatted_data
    
formatted_data = format_scraped_data(all_city_data)

# Output the formatted data
json_data=[]
for entry in formatted_data:
    json_data.append(entry)
final_json= {
"entity": "eTransportDirectory",
"data":json_data}

# Output as JSON (for display or saving to a file)
json = json.dumps(final_json, indent=4)
print(json)

# Optionally save the output to a file
with open('eTransportDirectory.json', 'w') as f:
    f.write(json)
