from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import time

# Set up Chrome options
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in headless mode (no GUI)
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Initialize the Chrome driver
driver = webdriver.Chrome(service=Service(), options=chrome_options)

# Function to extract data from a single entry
def scrape_entry_data(driver, index):
    try:
        entry_data = {
            "name": "",
            "address": "",
            "email": "",
            "website": "",
            "city": "",
            "state": "",
            "landlineNo": [],  # Should contain only landline numbers
            "contactPerson": [],
            "contactNo": "",  # Should contain all mobile numbers as a single string
            "gstNo": "",
            "companyRegistrationNo": "",
            "truckAvailable": [],  # Populate based on Category
            "services": [],
            "location": []  # Should be an array
        }

        entry_data['name'] = driver.find_element(By.XPATH, f"//*[@id='ContentPlaceHolder1_GridView1_COMPNA_{index}']").text
        entry_data['address'] = driver.find_element(By.XPATH, f"//*[@id='ContentPlaceHolder1_GridView1_div_home_{index}']/div[1]/p[4]/span").text

        # Extract all numbers and categorize them
        all_numbers = driver.find_element(By.XPATH, f"//*[@id='ContentPlaceHolder1_GridView1_div_home_{index}']/div[2]/ul/li[2]").text.split(', ')

        # Filter landline numbers (assuming they start with 0-6)
        entry_data['landlineNo'] = [num for num in all_numbers if num.startswith(("0", "1", "2", "3", "4", "5", "6"))]
        
        # Clean landline numbers to remove any mobile-related text
        entry_data['landlineNo'] = [num.split(" Mobile : ")[0] for num in entry_data['landlineNo']]

        # Filter mobile numbers (assuming they start with 7, 8, or 9)
        mobile_numbers = [num for num in all_numbers if num.startswith(("7", "8", "9"))]
        entry_data['contactNo'] = ', '.join(mobile_numbers)  # Combine mobile numbers into a single string

        entry_data['contactPerson'] = [driver.find_element(By.XPATH, f"//*[@id='ContentPlaceHolder1_GridView1_div_home_{index}']/div[3]/ul/li[2]").text]
        entry_data['services'] = [service.strip() for service in driver.find_element(By.XPATH, f"//*[@id='ContentPlaceHolder1_GridView1_div_home_{index}']/div[5]/ul/li[2]").text.split(',')]

        # Store location as an array, removing parentheses and trimming spaces
        raw_location = driver.find_element(By.XPATH, f"//*[@id='ContentPlaceHolder1_GridView1_div_home_{index}']/div[6]/ul/li[2]").text
        location_parts = [loc.strip().replace('(', '').replace(')', '') for loc in raw_location.split(',')]
        
        # Remove everything after "to" in the location field
        cleaned_location = []
        for part in location_parts:
            if 'to' in part:
                part = part.split('to')[0].strip()
            cleaned_location.append(part)
        
        entry_data['location'] = [loc for loc in cleaned_location if loc and loc != "All Over India"]  # Remove "All Over India"

        # Extract Category to determine truck availability
        category_text = driver.find_element(By.XPATH, f"//*[@id='ContentPlaceHolder1_GridView1_div_home_{index}']/div[4]/ul/li[2]").text
        entry_data['truckAvailable'] = [category.strip() for category in category_text.split(',') if category.strip()]  # Assuming categories are comma-separated

        return entry_data
    except Exception as e:
        print(f"Error extracting data from entry {index}: {e}")
        return None


# Function to extract data from the current page
def extract_data_from_page(driver):
    page_data = []
    for i in range(5):  # Assuming there are 5 entries per page
        data = scrape_entry_data(driver, i)
        if data:
            page_data.append(data)
    return page_data

# Function to navigate through pages and scrape data
def navigate_pages(driver, start_page, end_page):
    all_data = []
    for page in range(start_page, end_page + 1):  # Navigate through specified page range
        print(f"Scraping page {page}...")

        # Extract data from the current page
        page_data = extract_data_from_page(driver)
        all_data.extend(page_data)

        # Click on the button to navigate to the next page
        if page < end_page:
            try:
                button_xpath = f"//*[@id='ContentPlaceHolder1_GridView1']/tbody/tr[6]/td/table/tbody/tr/td[{page + 1}]"
                button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, button_xpath))
                )
                button.click()
                time.sleep(2)  # Wait for the page to load
            except Exception as e:
                print(f"Error navigating to button for page {page + 1}: {e}")
                break

    return all_data

# Function to navigate to the new set of pages via the hyperlink
def navigate_to_new_pages(driver, hyperlink_xpath, total_pages):
    print(f"Navigating to new pages via hyperlink {hyperlink_xpath}...")

    # Click the hyperlink to go to the new page set
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, hyperlink_xpath))
    ).click()

    time.sleep(2)  # Wait for the new page to load

    # Now scrape the additional pages using the same XPath
    new_page_data = navigate_pages(driver, 1, total_pages)  # Scrape pages 1 to total_pages
    return new_page_data

# Main logic
def main():
    driver.get("http://mtid.in/dashboard.aspx?cat_id=1&&sub_cat_id=1")  # Replace with the actual URL

    # Scrape the first 10 pages
    all_scraped_data = navigate_pages(driver, 1, 10)

    # Navigate to the first new set of pages and scrape 11 pages
    first_hyperlink = '//*[@id="ContentPlaceHolder1_GridView1"]/tbody/tr[6]/td/table/tbody/tr/td[11]/a'
    new_scraped_data = navigate_to_new_pages(driver, first_hyperlink, 11)
    all_scraped_data.extend(new_scraped_data)

    # From the 12th hyperlink onward, use the same XPath
    second_hyperlink = '//*[@id="ContentPlaceHolder1_GridView1"]/tbody/tr[6]/td/table/tbody/tr/td[12]/a'
    for _ in range(22):  # Assuming you want to scrape 21 more sets of pages
        new_scraped_data = navigate_to_new_pages(driver, second_hyperlink, 11)
        all_scraped_data.extend(new_scraped_data)

    # Wrap the data in the desired structure
    output_data = {
        "entity": "mudhra_publication",
        "data": all_scraped_data
    }

    # Save the formatted data to a JSON file
    with open('scraped_data.json', 'w') as json_file:
        json.dump(output_data, json_file, indent=4)

    print("Data successfully saved to scraped_data.json.")
    driver.quit()

if __name__ == "__main__":
    main()
