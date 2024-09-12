import sys
import time

from PyQt5.QtCore import QObject, pyqtSignal
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService


class PlayManager(QObject):  # Inherit QObject for threading
    finished = pyqtSignal()  # Signal to emit when the PlayManager is done

    def __init__(self, logger, elements, point_difference, refreshTime, game_window):
        super().__init__()  # Initialize QObject
        logger.info(f'Initializing the game manager...')
        self.logger = logger
        self.basketballUrl = ""
        self.url = ""
        self.username = ""
        self.password = ""
        self.point_difference = point_difference
        self.elements = elements
        self.refresh_elapse_time = refreshTime
        self.basketballLeagues = {}  # Dictionary to store leagues and their games
        self.marked_games = {}  # Dictionary to store games marked for betting
        self.stop_flag = False
        self.game_window = game_window  # Reference to the GameWindow instance
        self.attempt_count = 0
        self.max_attempts = 3

        # Make the window fullscreen and headless
        chrome_options = Options()
        # chrome_options.add_argument("--headless")  # This makes the browser invisible
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-software-rasterizer")
        # Create driver with retry logic
        self.driver = None
        self.retry_driver(chrome_options)

    def retry_driver(self, chrome_options, max_attempts=3):
        """Retries launching the WebDriver up to max_attempts in case of failure."""
        attempt_count = 0
        while attempt_count < max_attempts:
            try:

                self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()),
                                               options=chrome_options)
                self.logger.info("Chrome WebDriver successfully launched.")
                return
            except WebDriverException as e:
                self.logger.error(
                    f"WebDriver failed to launch: {str(e)}. Attempt {attempt_count + 1} of {max_attempts}.")
                attempt_count += 1

        self.logger.critical("Failed to launch WebDriver after several attempts. Exiting program.")
        raise Exception('Failed to load driver');

    def open_live_events_window(self, attempt_count, max_attempts, required_substring):
        while attempt_count < max_attempts:
            try:
                current_url = self.driver.current_url
                if required_substring not in current_url:
                    self.logger.warning(
                        f"URL does not contain '{required_substring}'. Attempting to navigate to the correct page...")
                    # Try to navigate to the correct page by clicking the first game link
                    league_headers = self.driver.find_elements(By.CLASS_NAME,
                                                               self.elements["consts"]['league_headers_class_name'])
                    for league_header in league_headers:
                        # Check if the league is already expanded (by checking its style attribute)
                        parent_div = league_header.find_element(By.XPATH,
                                                                self.elements["consts"][
                                                                    'league_header_container_xpath'])
                        if self.elements["consts"]['expanded_league_style'] in parent_div.get_attribute("style"):
                            # If the league is opened, find the first game link
                            first_game_link = parent_div.find_element(By.CLASS_NAME,
                                                                      self.elements["consts"][
                                                                          'first_game_link_class'])
                            first_game_link.click()
                            time.sleep(1)  # Wait for the game page to load
                            break

                    # Increment the attempt count
                    attempt_count += 1

                    # Check the URL again after attempting to navigate
                    current_url = self.driver.current_url
                    if required_substring in current_url:
                        self.logger.info("Successfully navigated to the correct page.")
                        return True  # Exit the loop if the URL is correct now
                    else:
                        self.logger.info("Already on the correct page.")
                        return True  # Exit the loop if the URL is already correct

            except Exception as e:
                self.logger.critical(f"Received an error during game loop: ${e}\n")
                return False  # Stop the method if the navigation was unsuccessful
            if attempt_count == max_attempts:
                self.logger.critical(
                    "Failed to navigate to the correct page after 3 attempts. Stopping the operation.")
                return False  # Stop the method if the navigation was unsuccessful

    def login(self, url, basketballUrl, username, password):
        try:
            self.logger.info('Logging in to the site...')
            self.url = url
            self.basketballUrl = basketballUrl
            self.username = username
            self.password = password

            # Open the login page
            self.driver.get(self.url)
            wait = WebDriverWait(self.driver, 10)

            # Find and fill the username and password fields, then submit the form
            username_field = wait.until(
                EC.presence_of_element_located((By.NAME, self.elements["consts"]['login_username_element_name'])))
            password_field = wait.until(
                EC.presence_of_element_located((By.NAME, self.elements["consts"]['login_password_element_name'])))
            login_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, self.elements["consts"]['login_bottom_xpath'])))

            username_field.send_keys(self.username)
            password_field.send_keys(self.password)
            login_button.click()

            # Wait for navigation to the main page after login
            time.sleep(3)
            # Navigate to the basketball page after login
            self.driver.get(self.basketballUrl)
            time.sleep(3)

            return self.open_live_events_window(self.attempt_count, self.max_attempts,
                                                self.elements["consts"]['live_events_suffix'])

        except TimeoutException as e:
            self.logger.error(f"Timeout error during login process: {str(e)}")
        except Exception as e:
            self.logger.critical(f"Received an error during game login process: {str(e)}")
            return False

    def update_game_window(self):
        """Updates the game window with the current leagues and games."""
        self.logger.info('Updating game window...')
        try:
            self.game_window.update_game_data(self.basketballLeagues, self.marked_games)
        except Exception as e:
            self.logger.error(f"Error updating game window: {str(e)}")

    def stop(self):
        """Stops the infinite loop in the play method."""
        self.logger.info('Stopping the game loop...')
        self.stop_flag = True

    def play(self):
        self.logger.info('Starting game monitoring...')
        try:
            while not self.stop_flag:
                if self.elements["consts"]['live_events_suffix'] not in self.driver.current_url:
                    self.open_live_events_window(self.attempt_count, self.max_attempts,
                                                 self.elements["consts"]['live_events_suffix'])
                # Collect game data and update the structure directly
                self.collect_game_data()

                # Handle the selected rows for betting
                self.handle_selected_rows()

                # Update the GameWindow with the latest game data
                self.update_game_window()

                time.sleep(self.refresh_elapse_time)
        except Exception as e:
            self.logger.error(f"Unexpected error during play method: {str(e)}")
        finally:
            if self.driver:
                self.driver.quit()  # Properly quit the browser
            self.finished.emit()

    def collect_game_data(self):
        self.logger.debug('Collecting games data...')
        wait = WebDriverWait(self.driver, 10)
        try:
            # Locate basketball section container
            basketball_section = wait.until(EC.presence_of_element_located(
                (By.XPATH, self.elements["consts"]['basketball_section_container_xpath'])))
            leagues = basketball_section.find_elements(By.CLASS_NAME, self.elements["consts"]['leagues_section_class'])

            previous_league_header = None
            current_games_lists = {}

            for league in leagues:
                try:
                    # Locate and expand the league header if needed
                    league_header = league.find_element(By.CLASS_NAME, self.elements["consts"]['leagues_header_class'])
                    league_name = league_header.text.strip()

                    if league_name not in self.basketballLeagues:
                        self.basketballLeagues[league_name] = {}

                    # Close the previous league if it was opened
                    if previous_league_header and self.elements["consts"][
                        'collapsed_league_class'] in previous_league_header.get_attribute('class'):
                        previous_league_header.click()

                    # Expand the current league if it's collapsed
                    if self.elements["consts"]['collapsed_league_class'] not in league_header.get_attribute('class'):
                        league_header.click()

                    # Collect data from each game in the league
                    games = league.find_elements(By.CLASS_NAME, self.elements["consts"]['games_in_league_class'])
                    for game in games:
                        try:
                            self.collect_game_info(game, league_name, current_games_lists)
                        except Exception as e:
                            self.logger.warning(f"Error collecting data for a game in league {league_name}: {e}")

                    previous_league_header = league_header
                except NoSuchElementException as e:
                    self.logger.warning(f"Error processing league: {e}")
                    continue

            # Remove games that are no longer active
            self.clean_up_inactive_games(current_games_lists)

        except TimeoutException as e:
            self.logger.warning(f"Error in collect_game_data: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error in collect_game_data: {str(e)}")

    def collect_game_info(self, game, league_name, current_games_lists):
        """Helper method to collect information for a specific game."""
        try:
            # Click on the game to open its details
            game.click()
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, self.elements["consts"]['first_team_name_class'])))

            # Collect game data
            first_team_name = game.find_element(By.CLASS_NAME, self.elements["consts"]['first_team_name_class']).text
            second_team_name = game.find_element(By.CLASS_NAME, self.elements["consts"]['second_team_name_class']).text
            team_scores = game.find_elements(By.CLASS_NAME, self.elements["consts"]['game_scores_pair_section'])

            first_team_score = team_scores[0].text if len(team_scores) >= 2 else team_scores[0].text
            second_team_score = team_scores[1].text if len(team_scores) >= 2 else team_scores[0].text
            quarter_number = game.find_element(By.CLASS_NAME, self.elements["consts"]['quarter_number_class']).text
            time_left = game.find_element(By.CLASS_NAME, self.elements["consts"]['time_left_class']).text

            game_key = f"{first_team_name} vs {second_team_name}"

            if league_name not in current_games_lists:
                current_games_lists[league_name] = []
            if game_key not in current_games_lists[league_name]:
                current_games_lists[league_name].append(game_key)

            game_data = {
                self.elements['consts']['first_team']: first_team_name,
                self.elements['consts']['second_team']: second_team_name,
                self.elements['consts']['first_team_score']: first_team_score,
                self.elements['consts']['second_team_score']: second_team_score,
                self.elements['consts']['total_score']: (int(first_team_score) + int(second_team_score)),
                self.elements['consts']['quarter_number']: quarter_number,
                self.elements['consts']['time_left']: time_left
            }

            # Add new game or update existing one
            if game_key in self.basketballLeagues[league_name]:
                self.update_game_data(game_key, game_data, league_name)
            else:
                self.add_new_game(game_key, game_data, league_name)

        except NoSuchElementException as e:
            self.logger.warning(f"Could not collect data for game a in league {league_name}: {str(e)}")
        except TimeoutException as e:
            self.logger.warning(
                f"Timeout while collecting game info for a game in league {league_name}: {str(e)}")

    def add_new_game(self, game_key, game_data, league_name):
        self.logger.debug(f'Adding new game: {game_key}')
        try:
            # Handle the case where the game has not started yet
            if game_data[self.elements['consts']['quarter_number']] == self.elements['consts']['ATS']:
                self.basketballLeagues[league_name][game_key] = game_data
            else:
                # The game is in progress, capture the first total score
                first_total_row = self.find_first_total_in_table(game_key)

                if first_total_row and first_total_row[self.elements['consts']['total_text_value']]:
                    game_data[self.elements['consts']['first_total_score']] = first_total_row[
                        self.elements['consts']['total_text_value']]
                    game_data[self.elements['consts']['quarter_when_recorded']] = game_data[
                        self.elements['consts']['quarter_number']]
                    game_data[self.elements['consts']['time_left_when_recorded']] = game_data[
                        self.elements['consts']['time_left']]
                    self.basketballLeagues[league_name][game_key] = game_data
                else:
                    self.basketballLeagues[league_name][game_key] = False

        except Exception as e:
            self.logger.error(f"Error adding new game {game_key}: {str(e)}")

    def update_game_data(self, game_key, game_data, league_name):
        try:
            self.logger.debug(f'Updating game {game_data} data')
            existing_game = self.basketballLeagues[league_name][game_key]
            # Handle ATS and B quarter cases
            if game_data[self.elements['consts']['quarter_number']] == self.elements['consts']['ATS']:
                # Do not update anything if the game is still in ATS
                return
            elif game_data[self.elements['consts']['quarter_number']] == self.elements['consts']['B']:
                # Do not update during break periods
                return
            elif (existing_game[self.elements['consts']['quarter_number']] == self.elements['consts']['ATS']
                  and game_data[self.elements['consts']['quarter_number']] == self.elements['consts']['1Q']):
                # Update first_total_score only if quarter 1Q just started
                if (existing_game[self.elements['consts']['time_left']] == self.elements['consts']['10:00'] and
                        (game_data[self.elements['consts']['time_left']] == self.elements['consts']['09:59']
                         or game_data[self.elements['consts']['time_left']] == self.elements['consts']['09:59'])):
                    # The game is in progress, capture the first total score
                    first_total_row = self.find_first_total_in_table(game_key)

                    existing_game[self.elements['consts']['first_total_score']] = int(first_total_row[
                        self.elements['consts']['total_text_value']])
                    existing_game[self.elements['consts']['quarter_when_recorded']] = self.elements['consts']['1Q']
                    existing_game[self.elements['consts']['time_left_when_recorded']] = self.elements['consts']['10:00']
                existing_game.update(game_data)
            else:
                # Regular update for the game
                existing_game.update(game_data)
        except Exception as e:
            self.logger.error(f"Error updating game {game_key}: {str(e)}")

    def handle_selected_rows(self):
        """Selects the suitable rows from the total table based on game data."""
        self.logger.debug('Selecting suitable total row from table for betting')
        try:
            for league_name, games in self.basketballLeagues.items():
                for game_key, game_data in games.items():
                    if self.elements['consts']['first_total_score'] in game_data:
                        # Find the suitable row for betting
                        selected_row = self.find_total_table(game_data[self.elements['consts']['first_total_score']])
                        if selected_row:
                            # Mark the game for betting
                            self.marked_games[game_key] = {
                                self.elements['consts']['league_name_field']: league_name,
                                self.elements['consts']['selected_row_field']: selected_row
                            }
                            self.logger.debug(
                                f"Marked Game: {game_key} in League: {league_name}, Selected Row: {selected_row}")
        except Exception as e:
            self.logger.warning(f"Error selecting total row for betting: {e}")

    def clean_up_inactive_games(self, active_games):
        """Remove games that are no longer active from the dictionary."""
        self.logger.debug(f'Cleaning up inactive games...')
        try:
            for league_name in list(self.basketballLeagues.keys()):
                for game_key in list(self.basketballLeagues[league_name].keys()):
                    if game_key not in active_games[league_name]:
                        self.logger.info(f'Cleaning up inactive game: {game_key}')
                        del self.basketballLeagues[league_name][game_key]

                # Remove leagues that no longer have active games
                if league_name not in active_games or not self.basketballLeagues[league_name]:
                    self.logger.info(f'Cleaning up empty league: {league_name}')
                    del self.basketballLeagues[league_name]
        except Exception as e:
            self.logger.error(f"Error cleaning up inactive games: {str(e)}")

    def find_first_total_in_table(self, game_key):
        """Finds the first row in the total table."""
        self.logger.debug(f'Searching for the first row in the total table for game {game_key}')
        try:
            tables = self.driver.find_elements(By.CLASS_NAME, self.elements['consts']['total_table_class'])

            for table in tables:
                header = table.find_element(By.CLASS_NAME, self.elements['consts']['table_header_class'])
                header_text = header.find_element(By.CLASS_NAME,
                                                  self.elements['consts']['table_header_text_class']).text

                if header_text == self.elements['consts']['table_text_value']:
                    if self.elements['consts']['show_text_value'] not in table.get_attribute('class'):
                        table.click()

                    rows = table.find_elements(By.CLASS_NAME, self.elements['consts']['table_rows_class'])
                    first_row = rows[0]

                    expected_total_score = float(
                        first_row.find_element(By.CLASS_NAME,
                                               self.elements['consts']['table_row_total_score_class']).text)
                    over_value = float(
                        first_row.find_elements(By.CLASS_NAME, self.elements['consts']['table_row_over_score_class'])[
                            0].text)
                    under_value = float(
                        first_row.find_elements(By.CLASS_NAME, self.elements['consts']['table_row_under_score_class'])[
                            1].text)

                    return {
                        self.elements['consts']['total_text_value']: expected_total_score,
                        self.elements['consts']['over_text_value']: over_value,
                        self.elements['consts']['under_text_value']: under_value
                    }
            return None
        except Exception as e:
            self.logger.warning(f"Error finding first total in table for game {game_key}: {e}")
            return None

    def find_total_table(self, game_first_total_score):
        """Finds a suitable row in the total table based on the first total score of the game."""
        self.logger.debug('Finding total table based on first total score')
        try:
            tables = self.driver.find_elements(By.CLASS_NAME, self.elements['consts']['total_table_class'])

            for table in tables:
                header = table.find_element(By.CLASS_NAME, self.elements['consts']['table_header_class'])
                header_text = header.find_element(By.CLASS_NAME,
                                                  self.elements['consts']['table_header_text_class']).text

                if header_text == self.elements['consts']['table_text_value']:
                    if self.elements['consts']['show_text_value'] not in table.get_attribute('class'):
                        table.click()

                    suitable_rows = self.extract_suitable_rows(table, game_first_total_score)

                    if suitable_rows:
                        return min(suitable_rows, key=lambda x: x[self.elements['consts']['under_text_value']])
            return None
        except Exception as e:
            self.logger.warning(f"Error finding total table: {e}")
            return None

    def extract_suitable_rows(self, total_table, game_first_total_score):
        """Extracts rows that meet the betting criteria."""
        suitable_rows = []
        try:
            rows = total_table.find_elements(By.CLASS_NAME, self.elements['consts']['table_rows_class'])

            for row in rows:
                expected_total_score = float(
                    row.find_element(By.CLASS_NAME, self.elements['consts']['table_row_total_score_class']).text)
                over_value = float(
                    row.find_elements(By.CLASS_NAME, self.elements['consts']['table_row_over_score_class'])[0].text)
                under_value = float(
                    row.find_elements(By.CLASS_NAME, self.elements['consts']['table_row_under_score_class'])[1].text)

                if expected_total_score >= game_first_total_score + self.point_difference and under_value >= 1.8:
                    suitable_rows.append({
                        self.elements['consts']['total_text_value']: expected_total_score,
                        self.elements['consts']['over_text_value']: over_value,
                        self.elements['consts']['under_text_value']: under_value
                    })
            return suitable_rows
        except Exception as e:
            self.logger.warning(f"Error extracting suitable rows from total table: {e}")
            return suitable_rows
