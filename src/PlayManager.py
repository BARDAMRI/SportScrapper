import time
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException, \
    ElementClickInterceptedException, StaleElementReferenceException

from selenium.webdriver.common.by import By

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class PlayManager(QObject):  # Inherit QObject for threading
    finished = pyqtSignal()  # Signal to emit when the PlayManager is done
    data_updated = pyqtSignal(dict, dict)

    def __init__(self, driver, logger, max_try_count, elements, point_difference, refreshTime, game_window):
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
        self.max_attempts = max_try_count
        self.driver = driver

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
                            if first_game_link is not None:
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
                self.logger.critical(f"Received an error during game loop: {e}\n")
                return False  # Stop the method if the navigation was unsuccessful
            if attempt_count == max_attempts:
                self.logger.critical(
                    "Failed to navigate to the correct page after 3 attempts. Stopping the operation.")
                return False  # Stop the method if the navigation was unsuccessful

    def login(self, url, basketballUrl, username, password):
        curr_retry = 0
        while curr_retry < self.max_attempts:
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
                if login_button is not None:
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
                curr_retry += 1

            except Exception as e:
                self.logger.critical(f"Received an error during game login process: {str(e)}")
                curr_retry += 1
        return False

    @pyqtSlot(bool)
    def stop(self, stopping=True):
        """Stops the infinite loop in the play method."""
        self.logger.info('Stopping the game loop...')
        self.stop_flag = True

    def play(self):
        self.logger.info('Starting game monitoring...')
        try:
            while not self.stop_flag:  # Make sure to check for this flag
                # Your game monitoring logic
                if self.elements["consts"]['live_events_suffix'] not in self.driver.current_url:
                    self.open_live_events_window(self.attempt_count, self.max_attempts,
                                                 self.elements["consts"]['live_events_suffix'])
                self.collect_game_data()

                # Emit the latest game data to the UI
                self.data_updated.emit(self.basketballLeagues, self.marked_games)

                time.sleep(self.refresh_elapse_time)  # Adjust refresh time to prevent blocking
        except Exception as e:
            self.logger.error(f"Unexpected error during play method: {str(e)}")

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
                    if (previous_league_header and self.elements["consts"][
                            'collapsed_league_class'] in previous_league_header.get_attribute('class')):
                        previous_league_header.click()

                    # Expand the current league if it's collapsed
                    if self.elements["consts"]['collapsed_league_class'] not in league_header.get_attribute('class'):
                        league_header.click()

                    # Collect data from each game in the league
                    games = league.find_elements(By.CLASS_NAME, self.elements["consts"]['games_in_league_class'])
                    for index, game in enumerate(games):
                        try:
                            self.collect_game_info(index, game, league_name, current_games_lists)
                        except Exception as e:
                            try:
                                g = game.find_element(By.CLASS_NAME,
                                                      self.elements["consts"]['first_team_name_class']).text
                            except Exception:
                                g = 'Unknown'
                            self.logger.warning(
                                f"Error collecting data for a game of team {g} in league {league_name}: {e}")

                    previous_league_header = league_header
                except (NoSuchElementException, Exception) as e:
                    self.logger.warning(f"Error processing league: {e}")
                    continue

            # Remove games that are no longer active
            self.clean_up_inactive_games(current_games_lists)

        except (TimeoutException, Exception) as e:
            self.logger.warning(f"Error in collect_game_data: {str(e)}")

    def collect_game_info(self, game_index, game, league_name, current_games_lists):
        """Helper method to collect information for a specific game."""
        try:
            self.logger.info(f'Clicking game at league {league_name} at index {game_index}.')
            game.click()
            # Collect game data
            self.logger.info(f'Starting collect game data...')
            first_team_name = game.find_element(By.CLASS_NAME, self.elements["consts"]['first_team_name_class']).text
            second_team_name = game.find_element(By.CLASS_NAME, self.elements["consts"]['second_team_name_class']).text
            team_scores = game.find_elements(By.CLASS_NAME, self.elements["consts"]['game_scores_pair_section'])

            first_team_score = team_scores[0].text if len(team_scores) >= 2 else 0
            second_team_score = team_scores[1].text if len(team_scores) >= 2 else 0
            quarter_number = game.find_element(By.CLASS_NAME, self.elements["consts"]['quarter_number_class']).text
            time_left = game.find_element(By.CLASS_NAME, self.elements["consts"]['time_left_class']).text

            self.logger.info(f'Creating key...')
            game_key = f"{first_team_name} vs {second_team_name}"

            self.logger.info(f'Inserting into games list...')
            if league_name not in current_games_lists:
                current_games_lists[league_name] = []
            if game_key not in current_games_lists[league_name]:
                current_games_lists[league_name].append(game_key)

            self.logger.info(f'Inserting into games list...')
            if (first_team_name == '' or second_team_name == '' or first_team_score == 'N/A' or
                    second_team_score == 'N/A' or quarter_number == 'NS' or time_left == '--:--'):
                self.logger.info(f'The game {game_key} has no 2 team names or score. cannot collect. ')
                return

            self.logger.info(f'Creating game object...')
            game_data = {
                self.elements['consts']['first_team']: first_team_name,
                self.elements['consts']['second_team']: second_team_name,
                self.elements['consts']['first_team_score']: first_team_score,
                self.elements['consts']['second_team_score']: second_team_score,
                self.elements['consts']['total_score']: (int(first_team_score) + int(second_team_score)),
                self.elements['consts']['quarter_number']: quarter_number,
                self.elements['consts']['time_left']: time_left
            }

            self.logger.info(f'Updating game on collections')
            # Add new game or update existing one
            if game_key in self.basketballLeagues[league_name]:
                self.update_game_data(game_key, game_data, league_name)
            else:
                self.add_new_game(game_key, game_data, league_name)

        except (ElementClickInterceptedException, NoSuchElementException, TimeoutException, Exception) as e:
            self.logger.warning(
                f"Exception on collect_game_info for game at index {game_index} in league {league_name}: {e}"
                f" Retrying...")
            time.sleep(1)
            self.collect_game_info(game_index, game, league_name, current_games_lists)  # Retry

    def add_new_game(self, game_key, game_data, league_name):
        self.logger.debug(f'Adding new game: {game_key}')
        try:
            # Handle the case where the game has not started yet
            game_data[self.elements['consts']['first_total_score']] = None
            game_data[self.elements['consts']['quarter_when_recorded']] = None
            game_data[self.elements['consts']['time_left_when_recorded']] = None

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
        except Exception as e:
            self.logger.error(f"Error adding new game {game_key}: {str(e)}")

    def update_game_data(self, game_key, game_data, league_name):
        try:
            self.logger.debug(f'Updating game {game_data} data')
            # Checking if game needed to be add as new game.
            existing_game = self.basketballLeagues[league_name][game_key]
            # Handle ATS and B quarter cases that does not should be updated.
            if (game_data[self.elements['consts']['quarter_number']] == self.elements['consts']['ATS'] or
                    self.elements['consts']['B'] in game_data[self.elements['consts']['quarter_number']]):
                return
            # Check if we moved from ats to 1Q value before game starts.
            if (existing_game['first_total_score'] and existing_game[self.elements['consts']['quarter_number']] ==
                    self.elements['consts']['ATS'] and game_data[self.elements['consts']['quarter_number']] ==
                    self.elements['consts']['1Q']):
                first_total_row = self.find_first_total_in_table(game_key)
                if first_total_row:
                    game_data[self.elements['consts']['first_total_score']] = first_total_row[
                        self.elements['consts']['total_text_value']]
                    game_data[self.elements['consts']['quarter_when_recorded']] = self.elements['consts']['1Q']
                    game_data[self.elements['consts']['time_left_when_recorded']] = self.elements['consts']['10:00']

            # Update new values.
            for key in list(game_data.keys()):
                existing_game[key] = game_data[key]
            self.check_table_mark(league_name, game_key, existing_game)
        except Exception as e:
            self.logger.error(f"Error updating game data {game_key}: {str(e)}")

    def check_table_mark(self, league_name, game_key, game_data):
        try:
            if (self.elements['consts']['first_total_score'] and self.elements['consts'][
                'first_total_score'] in game_data
                    and game_data[self.elements['consts']['first_total_score']]):
                # Find the suitable row for betting
                selected_row = self.find_selected_total_row(
                    game_data[self.elements['consts']['first_total_score']])
                if selected_row:
                    # Mark the game for betting
                    self.marked_games[game_key] = {
                        self.elements['consts']['league_name']: league_name,
                        self.elements['consts']['selected_row_field']: selected_row
                    }
                    self.logger.debug(
                        f"Marked Game: {game_key} in League: {league_name}, Selected Row: {selected_row}")
        except Exception as e:
            self.logger.warn(f'Exception during check_table_mark: {e}')

    def handle_selected_rows(self):
        """Selects the suitable rows from the total table based on game data."""
        self.logger.debug('Selecting suitable total row from table for betting')
        try:
            for league_name, games in self.basketballLeagues.items():
                for game_key, game_data in games.items():
                    if self.elements['consts']['first_total_score']:
                        # Find the suitable row for betting
                        if not game_data[self.elements['consts']['first_total_score']]:
                            selected_row = self.find_selected_total_row(
                                game_data[self.elements['consts']['first_total_score']])
                            if selected_row:
                                # Mark the game for betting
                                self.marked_games[game_key] = {
                                    self.elements['consts']['league_name_field']: league_name,
                                    self.elements['consts']['selected_row_field']: selected_row
                                }
                                self.logger.debug(
                                    f"Marked Game: {game_key} in League: {league_name}, Selected Row: {selected_row}")
        except Exception as e:
            self.logger.warning(f"Error selecting total row for betting in handle_selected_rows: {e}")

    def clean_up_inactive_games(self, active_games):
        """Remove games that are no longer active from the dictionary."""
        self.logger.debug(f'Cleaning up inactive games...')
        try:
            for league_name in list(self.basketballLeagues.keys()):

                games_list = []
                if league_name in self.basketballLeagues:
                    games_list = list(self.basketballLeagues[league_name].keys())
                for game_key in games_list:
                    if game_key not in active_games[league_name]:
                        self.logger.info(f'Cleaning up inactive game: {game_key}')
                        del self.basketballLeagues[league_name][game_key]

                # Remove leagues that no longer have active games
                if league_name not in active_games or not league_name in self.basketballLeagues:
                    self.logger.info(f'Cleaning up empty league: {league_name}')
                    del self.basketballLeagues[league_name]
        except Exception as e:
            self.logger.error(f"Error cleaning up inactive games: {e}")

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
            self.logger.warning(f"Error finding first total in table for game {game_key}")
            return None

    def find_selected_total_row(self, game_first_total_score):
        """Finds a suitable row in the total table based on the first total score of the game."""
        self.logger.debug('Finding total table based on first total score')
        table_index = -1
        rows_count = -1
        curr_row_index = 0
        obj_values = []
        under_values = []
        try:
            tables = self.driver.find_elements(By.CLASS_NAME, self.elements['consts']['total_table_class'])

            if table_index == -1:
                # get the table and store its index .
                for index, table in enumerate(tables):
                    header = table.find_element(By.CLASS_NAME, self.elements['consts']['table_header_class'])
                    header_text = header.find_element(By.CLASS_NAME,
                                                      self.elements['consts']['table_header_text_class']).text
                    if header_text == self.elements['consts']['table_text_value']:
                        table_index = index
                        if self.elements['consts']['show_text_value'] not in table.get_attribute('class'):
                            table.click()
                        rows = tables[table_index].find_elements(By.CLASS_NAME,
                                                                 self.elements['consts']['table_rows_class'])
                        rows_count = len(rows)
                        break
            # Iterate the table rows and fill the data lists.
            while curr_row_index < rows_count:
                # refresh the tables data and extract the row data.
                try:
                    res = self.extract_suitable_rows(table_index, curr_row_index, game_first_total_score)
                    if res:
                        if res == -1:
                            # out of index
                            break
                        if res != 0:
                            under = res[self.elements['consts']['under_text_value']]
                            under_values.append(under)
                            obj_values.append(res)
                        curr_row_index += 1
                except StaleElementReferenceException:
                    print(f"StaleElementReferenceException: Retrying row {curr_row_index} in the table")
            # Extract min value
            min_index = 0
            if len(under_values) == 0:
                return None
            min_value = under_values[0]
            for index, val in enumerate(under_values):
                if val < min_value:
                    min_index = index
                    min_value = val

            if min_index == -1:
                return None
            return obj_values[min_index]
        except Exception as e:
            self.logger.warning(f"Error finding total row.")
            return None

    def extract_suitable_rows(self, table_index, curr_row_index, game_first_total_score):
        """"
         :param table_index:  the total table index in the page tables list.
         :param curr_row_index: the current row needed to be extracted. needed in case of exception.
         :param game_first_total_score: the first total score value for the predicate.
         :return: -1 in case of rows list changed and needed to be continue.
                 0 in case the row doesn't accept the predicate.
                 [total, under, over] in case the row accepts the predicate.
                 None in case exception occurred and retry needed here.
         """
        try:
            tables = self.driver.find_elements(By.CLASS_NAME, self.elements['consts']['total_table_class'])
            rows = tables[table_index].find_elements(By.CLASS_NAME, self.elements['consts']['table_rows_class'])
            if len(rows) <= curr_row_index:
                return -1
            row = rows[curr_row_index]
            expected_total_score = float(
                row.find_element(By.CLASS_NAME, self.elements['consts']['table_row_total_score_class']).text)
            over_value = float(
                row.find_elements(By.CLASS_NAME, self.elements['consts']['table_row_over_score_class'])[0].text)
            under_value = float(
                row.find_elements(By.CLASS_NAME, self.elements['consts']['table_row_under_score_class'])[1].text)
            if ((game_first_total_score is not None and game_first_total_score >= 0)
                    and (self.point_difference is not None)
                    and (expected_total_score is not None and expected_total_score >= 0)
                    and (under_value is not None and under_value >= 0)
                    and self.elements['consts']['min_under_value']
                    and self.elements['consts']['total_text_value']
                    and self.elements['consts']['under_text_value']
                    and self.elements['consts']['over_text_value']
                    and under_value >= self.elements['consts']['min_under_value']
                    and expected_total_score - self.point_difference >= game_first_total_score):
                return {
                    self.elements['consts']['total_text_value']: expected_total_score,
                    self.elements['consts']['over_text_value']: over_value,
                    self.elements['consts']['under_text_value']: under_value,
                    self.elements['consts']['curr_row_index']: curr_row_index
                }
            else:
                return 0
        except Exception as err:
            return None
