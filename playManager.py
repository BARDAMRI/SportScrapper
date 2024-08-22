from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
import time
from selenium.webdriver.support import expected_conditions as EC

global first_team_score, second_team_name, first_team_name, second_team_score, quarter_number, time_left


class playManager():
    def __init__(self, elements, point_difference, refreshTime):
        self.basketballUrl = ""
        self.url = ""
        self.username = ""
        self.password = ""
        self.point_difference = point_difference
        self.elements = elements
        self.refresh = refreshTime
        self.games = {}
        self.leagues = {}
        self.marked_games = {}

        # Make the window fullscreen
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--start-fullscreen")

        # Create driver
        self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)

    def login(self, url, basketballUrl, username, password):
        print('Logging in to the site...')
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
        time.sleep(5)

        # Navigate to the basketball page after login
        self.driver.get(self.basketballUrl)
        time.sleep(5)

        # Find all league headers
        league_headers = self.driver.find_elements(By.CLASS_NAME, 'e4432ae')
        for league_header in league_headers:
            # Check if the league is already expanded (by checking its style attribute)
            parent_div = league_header.find_element(By.XPATH, "./following-sibling::div")
            if "height: auto;" in parent_div.get_attribute("style"):
                # If the league is opened, find the first game link
                first_game_link = parent_div.find_element(By.CLASS_NAME, 'f3191bc')
                first_game_link.click()
                time.sleep(1)  # Wait for the game page to load
                break

    def play(self):
        print('Starting game monitoring...')

        try:
            while True:
                # Collect game data
                game_data = self.collect_game_data()

                # Print the collected data
                # self.print_game_data(game_data)

                # Pause for the refresh time before the next iteration
                time.sleep(self.refresh)

        except Exception as e:
            print(f"Faced an error during play method operation: {e}")

    def collect_game_data(self):
        # Collect data for all leagues and their games
        global first_team_score, second_team_name, first_team_name, second_team_score, quarter_number, time_left
        game_data = []
        basketball_section = self.driver.find_element(By.XPATH, "//div[@data-sportid='2']/following-sibling::div")

        leagues = basketball_section.find_elements(By.CLASS_NAME, 'b537635')
        previous_league_header = None

        for lPosition in range(len(leagues)):
            league = leagues[lPosition]
            league_header = league.find_element(By.CLASS_NAME, 'fb51a4d')

            # Close the previous league if it was opened
            if previous_league_header:
                previous_league_header.click()
                time.sleep(1)  # Wait for the league to collapse

            # Expand the current league if it's collapsed
            if 'd49b804' not in league.get_attribute('class'):
                league_header.click()
                time.sleep(1)  # Wait for the league to expand

            # Re-find all games in the current league after expanding
            games = league.find_elements(By.CLASS_NAME, 'bcb4679')
            for position in range(len(games)):
                game = games[position]
                try:
                    # Locate elements by the first class and verify the second class
                    first_team_name_elem = game.find_element(By.CLASS_NAME, 'ed51694')
                    first_team_name = first_team_name_elem.text

                    second_team_name_elem = game.find_element(By.CLASS_NAME, 'e333ea9')
                    second_team_name = second_team_name_elem.text

                    team_scores = game.find_elements(By.CLASS_NAME, 'd12a5bc')

                    # Assuming the first element corresponds to the first team's score and the second to the second team's score
                    if len(team_scores) >= 2:
                        first_team_score = team_scores[0].text
                        second_team_score = team_scores[1].text
                    else:
                        first_team_score = second_team_score = team_scores[0].text

                    quarter_number_elem = game.find_element(By.CLASS_NAME, 'c669e6b')
                    quarter_number = quarter_number_elem.text

                    time_left_elem = game.find_element(By.CLASS_NAME, 'e5892ca')
                    time_left = time_left_elem.text

                    newGame = {
                        'first_team': first_team_name,
                        'second_team': second_team_name,
                        'first_team_score': first_team_score,
                        'second_team_score': second_team_score,
                        'quarter_number': quarter_number,
                        'time_left': time_left
                    }
                    self.print_game_data([newGame])
                    # Store collected data
                    game_data.append(newGame)

                except Exception as e:
                    print(f"Error collecting data for a game: {e}")
                    continue

            # Update previous_league_header to current
            previous_league_header = league_header

        return game_data

    def print_game_data(self, game_data):
        # Print the collected game data
        for game in game_data:
            print(f"Game: {game['first_team']} vs {game['second_team']}")
            print(f"Scores: {game['first_team_score']} - {game['second_team_score']}")
            print(f"Quarter: {game['quarter_number']}, Time Left: {game['time_left']}")
            print("=" * 40)
