from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd  # Import pandas for DataFrame and Excel export
import time  # Import time for waiting

options = webdriver.ChromeOptions()
options.add_argument("--disable-blink-features=AutomationControlled") 
options.add_experimental_option("excludeSwitches", ["enable-automation"]) 
options.add_experimental_option("useAutomationExtension", False)
options.add_argument("--incognito")
options.add_argument("--disable-extensions")  # Disable extensions
options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
options.add_experimental_option("prefs", {
    "profile.managed_default_content_settings.images": 2,  # Disable images
    "profile.managed_default_content_settings.javascript": 2  # Disable JavaScript
})
# Using ChromeDriverManager to automatically install chromedriver
service = Service(ChromeDriverManager().install())

# Initialize the browser with Service
driver = webdriver.Chrome(service=service,options=options)
driver.set_window_size(1400,900)
driver.set_window_position(500, 0)
driver.set_page_load_timeout(30)
# Initialize a list to store the data
data_list = []

# Define a function to extract data from the current page
def extract_data_from_page():
    # Loop through the houses from div:nth-child(1) to div:nth-child(25)
    for i in range(1, 30):  # 1 to 25
        try:
            # Build CSS selector for each house
            house_selector = f'#product-lists-web > div:nth-child({i}) > a > div.re__card-info > div.re__card-info-content > h3 > span'
            
            # Find and click on the house
            house_element = driver.find_element(By.CSS_SELECTOR, house_selector)
            house_element.click()

            # Wait for the detail page to load
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, 'h1')))  # Wait for the page title to load
            
            # Get HTML of the detail page
            detail_html = driver.page_source
            
            # Parse HTML with BeautifulSoup
            detail_soup = BeautifulSoup(detail_html, "html.parser")
            
            # Get the project title from the detail page
            project_title_element = detail_soup.select_one('#product-detail-web > span')
            project_title = project_title_element.text.strip() if project_title_element else None  # Get text or None if not found
            
            # Initialize a dictionary to hold the data for this house
            house_data = {
                "Dự án": project_title,
                "Diện tích": None,
                "Mức giá": None,
                "Giá tiền/m²": None,  # New field for price per square meter
                "Mặt tiền": None,
                "Đường vào": None,
                "Hướng nhà": None,
                "Hướng ban công": None,
                "Số tầng": None,
                "Số phòng ngủ": None,
                "Số toilet": None,
                "Pháp lý": None,
                "Nội thất": None,
            }

            # Extract required information
            spec_items = detail_soup.find_all('span', class_='re__pr-specs-content-item-value')
            for spec_item in spec_items:
                spec_title = spec_item.find_previous('span', class_='re__pr-specs-content-item-title').text.strip()
                spec_value = spec_item.text.strip()
                if "Diện tích" in spec_title:
                    house_data["Diện tích"] = spec_value
                elif "Mức giá" in spec_title:
                    house_data["Mức giá"] = spec_value
                elif "Mặt tiền" in spec_title:
                    house_data["Mặt tiền"] = spec_value
                elif "Đường vào" in spec_title:
                    house_data["Đường vào"] = spec_value
                elif "Hướng nhà" in spec_title:
                    house_data["Hướng nhà"] = spec_value
                elif "Hướng ban công" in spec_title:
                    house_data["Hướng ban công"] = spec_value
                elif "Số tầng" in spec_title:
                    house_data["Số tầng"] = spec_value
                elif "Số phòng ngủ" in spec_title:
                    house_data["Số phòng ngủ"] = spec_value
                elif "Số toilet" in spec_title:
                    house_data["Số toilet"] = spec_value
                elif "Pháp lý" in spec_title:
                    house_data["Pháp lý"] = spec_value
                elif "Nội thất" in spec_title:
                    house_data["Nội thất"] = spec_value

            # Extract price per square meter using the provided CSS selector
            price_per_m2_element = detail_soup.select_one('#product-detail-web > div.re__pr-short-info.entrypoint-v1.js__pr-short-info > div:nth-child(1) > span.ext')
            if price_per_m2_element:
                house_data["Giá tiền/m²"] = price_per_m2_element.text.strip()

            # Add the house data to the list only if at least one field has data
            if any(value is not None for value in house_data.values()):
                data_list.append(house_data)

            # Go back to the listing page after finishing
            driver.back()

            # Wait for the listing page to load again
            WebDriverWait(driver, 20).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.re__card-info > div.re__card-info-content > h3 > span')))

        except Exception as e:
            print(f"Đã xảy ra lỗi tại div:nth-child({i}): {e}")

# Loop to go through multiple pages by changing the URL
page_number = 452  # Start at page 1
max_pages = 841    # You can increase this to the number of pages you want to scrape

while page_number <= max_pages:
    # Generate the URL for the current page
    if page_number == 452:
        page_url = "https://batdongsan.com.vn/ban-nha-rieng-ha-noi/p452"
    else:
        page_url = f"https://batdongsan.com.vn/ban-nha-rieng-ha-noi/p{page_number}"
    
    # Navigate to the page
    driver.get(page_url)

    # Wait for the page to load completely
    WebDriverWait(driver, 20).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.re__card-info > div.re__card-info-content > h3 > span')))

    # Extract data from the current page
    extract_data_from_page()

    # Increment the page number
    page_number += 1

# Convert the data list to a DataFrame
df = pd.DataFrame(data_list)

# Save the DataFrame to an Excel file
df.to_excel("batdongsan_data.xlsx", index=False)

# Close the browser
driver.quit()
