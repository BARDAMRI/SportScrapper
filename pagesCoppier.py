from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import time
import os


def save_page(driver, output_path):
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(driver.page_source)


class Coppier():
    def __init__(self, url, basketballUrl, username, password):
        self.url = url
        self.basketballUrl = basketballUrl
        self.username = username
        self.password = password
        self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))

    def save_page(self, output_dir, filename="index.html"):
        page_source = self.driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        base_url = self.driver.current_url

        # Save main page
        main_page_path = os.path.join(output_dir, filename)
        with open(main_page_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))

        # Function to download and save linked resources
        def download_resource(link, attribute):
            resource_url = urljoin(base_url, link[attribute])
            resource_path = os.path.join(output_dir, urlparse(resource_url).path.lstrip('/'))

            # Ensure resource_path is a file, not a directory
            if resource_path.endswith('/'):
                resource_path = os.path.join(resource_path, 'index.html')

            os.makedirs(os.path.dirname(resource_path), exist_ok=True)
            resource_response = requests.get(resource_url)
            resource_response.raise_for_status()
            with open(resource_path, 'wb') as resource_file:
                resource_file.write(resource_response.content)
            link[attribute] = os.path.relpath(resource_path, output_dir)

        # Download and save CSS, JS, and images
        for tag in soup.find_all(['link', 'script', 'img']):
            if tag.has_attr('href'):
                download_resource(tag, 'href')
            if tag.has_attr('src'):
                download_resource(tag, 'src')

        # Save the updated HTML
        with open(main_page_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))

    def save_webpage(self, output_dir="webpage_copy"):
        # Open the login page
        self.driver.get(self.url)

        # Find and fill the username and password fields, then submit the form
        username_field = self.driver.find_element(By.NAME, "username")
        password_field = self.driver.find_element(By.NAME, "password")
        login_button = self.driver.find_element(By.XPATH, "//input[@type='submit' and @value='Login']")

        username_field.send_keys(self.username)
        password_field.send_keys(self.password)
        login_button.click()

        # Wait for the main page to load
        time.sleep(5)  # Adjust the sleep time as needed

        # Save the main page
        os.makedirs(output_dir, exist_ok=True)
        self.save_page(output_dir, "main_page.html")

        # Navigate to another page after login
        another_page_url = self.basketballUrl
        self.driver.get(another_page_url)
        time.sleep(50)  # Adjust the sleep time as needed

        # Save the new page
        self.save_page(output_dir, "another_page.html")

        # Close the WebDriver
        self.driver.quit()
