import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import time


class playManager():
    def __init__(self):
        self.basketballUrl = ""
        self.url = ""
        self.username = ""
        self.password = ""

        # Make the window fullscreen
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--start-fullscreen")

        # Create drive
        self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)

    def login(self, url, basketballUrl, username, password):
        print('Implementation needed on playManager -> login')
        self.url = url
        self.basketballUrl = basketballUrl
        self.username = username
        self.password = password
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

    def play(self):
        print('Implementation needed on playManager -> play')

        # Navigate to another page after login
        another_page_url = self.basketballUrl
        self.driver.get(another_page_url)

        time.sleep(50)  # Adjust the sleep time as needed

        continuePlay = True
