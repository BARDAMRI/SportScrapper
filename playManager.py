from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
import time
from selenium.webdriver.support import expected_conditions as EC


class playManager():
    def __init__(self, logger, elements, point_difference, refreshTime):
        logger.info(f'Initializing the game manager...')
        self.logger = logger
        self.basketballUrl = ""
        self.url = ""
        self.username = ""
        self.password = ""
        self.point_difference = point_difference
        self.elements = elements
        self.refresh = refreshTime
        self.basketballLeagues = {}  # Dictionary to store leagues and their games
        self.marked_games = {}  # Dictionary to store games marked for betting

        # Make the window fullscreen
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument(self.elements['consts']['full_screen_attribute'])

        # Create driver
        self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)

    def login(self, url, basketballUrl, username, password):
        self.logger.info('Logging in to the site...')
        self.url = url
        self.basketballUrl = basketballUrl
        self.username = username
        self.password = password

        # Open the login page
        self.driver.get(self.url)

        # Find and fill the username and password fields, then submit the form
        username_field = self.driver.find_element(By.NAME, self.elements["consts"]['login_username_element_name'])
        password_field = self.driver.find_element(By.NAME, self.elements["consts"]['login_password_element_name'])
        login_button = self.driver.find_element(By.XPATH, self.elements["consts"]['login_bottom_xpath'])

        username_field.send_keys(self.username)
        password_field.send_keys(self.password)
        login_button.click()

        # Wait for the main page to load
        time.sleep(3)

        # Navigate to the basketball page after login
        self.driver.get(self.basketballUrl)
        time.sleep(3)

        attempt_count = 0
        max_attempts = 3
        required_substring = "/sportsbook/live/events/"

        while attempt_count < max_attempts:
            current_url = self.driver.current_url

            if required_substring not in current_url:
                print(f"URL does not contain '{required_substring}'. Attempting to navigate to the correct page...")
                self.logger.warning(
                    f"URL does not contain '{required_substring}'. Attempting to navigate to the correct page...")
                # Try to navigate to the correct page by clicking the first game link
                league_headers = self.driver.find_elements(By.CLASS_NAME,
                                                           self.elements["consts"]['league_headers_class_name'])
                for league_header in league_headers:
                    # Check if the league is already expanded (by checking its style attribute)
                    parent_div = league_header.find_element(By.XPATH,
                                                            self.elements["consts"]['league_header_container_xpath'])
                    if self.elements["consts"]['expanded_league_style'] in parent_div.get_attribute("style"):
                        # If the league is opened, find the first game link
                        first_game_link = parent_div.find_element(By.CLASS_NAME,
                                                                  self.elements["consts"]['first_game_link_class'])
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

        if attempt_count == max_attempts:
            self.logger.critical("Failed to navigate to the correct page after 3 attempts. Stopping the operation.")
            return False  # Stop the method if the navigation was unsuccessful

    def play(self):
        self.logger.info('Starting game monitoring...')
        try:
            while True:
                # Collect game data and update the structure directly
                self.collect_game_data()

                # Handle the selected rows for betting
                self.handle_selected_rows()

                # Pause for the refresh time before the next iteration
                time.sleep(self.refresh)

        except Exception as e:
            self.logger.error(f"Faced an error during play method operation: {e}")

    def collect_game_data(self):
        global logger
        self.logger.debug('collecting games data...')
        basketball_section = self.driver.find_element(By.XPATH,
                                                      self.elements["consts"]['basketball_section_container_xpath'])

        leagues = basketball_section.find_elements(By.CLASS_NAME, self.elements["consts"]['leagues_section_class'])
        previous_league_header = None

        try:
            for lPosition in range(len(leagues)):
                league = leagues[lPosition]
                league_header = league.find_element(By.CLASS_NAME, self.elements["consts"]['leagues_header_class'])
                league_name = league_header.text.strip()

                # Initialize or update the league in the basketballLeagues dictionary
                if league_name not in self.basketballLeagues:
                    self.basketballLeagues[league_name] = {}

                # Close the previous league if it was opened
                if previous_league_header:
                    previous_league_header.click()
                    time.sleep(1)  # Wait for the league to collapse

                # Expand the current league if it's collapsed
                if self.elements["consts"]['collapsed_league_class'] not in league.get_attribute('class'):
                    league_header.click()
                    time.sleep(1)  # Wait for the league to expand

                # Re-find all games in the current league after expanding
                games = league.find_elements(By.CLASS_NAME, self.elements["consts"]['games_in_league_class'])
                for game in games:
                    try:
                        first_team_name = game.find_element(By.CLASS_NAME,
                                                            self.elements["consts"]['first_team_name_class']).text
                        second_team_name = game.find_element(By.CLASS_NAME,
                                                             self.elements["consts"]['second_team_name_class']).text
                        team_scores = game.find_elements(By.CLASS_NAME,
                                                         self.elements["consts"]['game_scores_pair_section'])

                        if len(team_scores) >= 2:
                            first_team_score = team_scores[0].text
                            second_team_score = team_scores[1].text
                        else:
                            first_team_score = second_team_score = team_scores[0].text

                        quarter_number = game.find_element(By.CLASS_NAME,
                                                           self.elements["consts"]['quarter_number_class']).text
                        time_left = game.find_element(By.CLASS_NAME, self.elements["consts"]['time_left_class']).text

                        # Create a unique game ID or key
                        game_key = f"{first_team_name} vs {second_team_name}"
                        if game_key in self.basketballLeagues[league_name] and not self.basketballLeagues[league_name]:
                            # game couldn't be initialized.
                            continue
                        # Store the game data in a dict format
                        game_data = {
                            self.elements['consts']['first_team']: first_team_name,
                            self.elements['consts']['second_team']: second_team_name,
                            self.elements['consts']['first_team_score']: first_team_score,
                            self.elements['consts']['second_team_score']: second_team_score,
                            self.elements['consts']['quarter_number']: quarter_number,
                            self.elements['consts']['time_left']: time_left,
                            self.elements['consts']['first_total_score']: None,
                            self.elements['consts']['quarter_when_recorded']: None,
                            self.elements['consts']['time_left_when_recorded']: None
                        }
                        # Check if the game is already in the league, update or add new
                        if game_key in self.basketballLeagues[league_name]:
                            self.update_game_data(game_key, game_data, league_name)
                        else:
                            self.add_new_game(game_key, game_data, league_name)

                    except Exception as e:
                        self.logger.warning(f"Error collecting data for a game: {e}")
                        continue

                # Update previous_league_header to current
                previous_league_header = league_header

            # Remove games that are no longer active
            self.clean_up_inactive_games(leagues)

        except Exception as e:
            self.logger.warning(f"Error in collect_game_data: {e}")

    def clean_up_inactive_games(self, active_leagues):
        self.logger.debug(f'Cleaning games...')
        active_game_keys = set()
        for league in active_leagues:
            league_games = league.find_elements(By.CLASS_NAME, self.elements["consts"]['games_in_league_class'])
            for game in league_games:
                first_team_name = game.find_element(By.CLASS_NAME,
                                                    self.elements["consts"]['first_team_name_class']).text
                second_team_name = game.find_element(By.CLASS_NAME,
                                                     self.elements["consts"]['second_team_name_class']).text
                game_key = f"{first_team_name} vs {second_team_name}"
                active_game_keys.add(game_key)

        # Remove games that are no longer in the active game keys
        for league_name in list(self.basketballLeagues.keys()):
            for game_key in list(self.basketballLeagues[league_name].keys()):
                if game_key not in active_game_keys:
                    self.logger.info(f'Cleaning game {game_key}')
                    del self.basketballLeagues[league_name][game_key]
            if not self.basketballLeagues[league_name]:  # Clean up empty leagues
                self.logger.info(f'Cleaning empty league {league_name}')
                del self.basketballLeagues[league_name]

    def add_new_game(self, game_key, game_data, league_name):
        self.logger.debug(f'Adding new game: {game_key}')
        if game_data[self.elements['consts']['quarter_number']] == self.elements['consts']['ATS']:
            # The game has not started yet, initialize without setting the first total score
            self.basketballLeagues[league_name][game_key] = game_data
        else:
            # The game has started or is in progress, we need to set the first total score and corresponding fields

            # Extract the first suitable row from the table
            first_total_row = self.find_first_total_in_table()

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

    def update_game_data(self, game_key, game_data, league_name):
        self.logger.debug(f'Updating game {game_data} data')
        existing_game = self.basketballLeagues[league_name][game_key]
        # Handle ATS and B quarter cases
        if game_data[self.elements['consts']['quarter_number']] == self.elements['consts']['ATS']:
            # Do not update anything if the game is still in ATS
            return
        elif game_data[self.elements['consts']['quarter_number']] == self.elements['consts']['B']:
            # Do not update during break periods
            return
        elif existing_game[self.elements['consts']['quarter_number']] == self.elements['consts']['ATS'] and game_data[
            self.elements['consts']['quarter_number']] == self.elements['consts']['1Q']:
            # Update first_total_score only if quarter 1Q just started
            if (game_data[self.elements['consts']['time_left']] == self.elements['consts']['10:00'] or
                    game_data[self.elements['consts']['time_left']] == self.elements['consts']['09:59']):
                existing_game[self.elements['consts']['first_total_score']] = int(
                    game_data[self.elements['consts']['first_team_score']]) + int(
                    game_data[self.elements['consts']['second_team_score']])
                existing_game[self.elements['consts']['quarter_when_recorded']] = self.elements['consts']['1Q']
                existing_game[self.elements['consts']['time_left_when_recorded']] = self.elements['consts']['10:00']
            existing_game.update(game_data)
        else:
            # Regular update for the game
            existing_game.update(game_data)

    def handle_selected_rows(self):
        self.logger.debug('choosing selected total row from table')
        # Iterate over all leagues and games
        try:
            for league_name, games in self.basketballLeagues.items():
                for game_key, game_data in games.items():
                    if game_data and game_data[self.elements['consts']['first_total_score']]:
                        # Find the suitable row for betting
                        selected_row = self.find_total_table(game_data[self.elements['consts']['first_total_score']])
                        if selected_row:
                            # Add or update the marked game with the selected row data
                            self.marked_games[game_key] = {
                                self.elements['consts']['league_name_field']: league_name,
                                self.elements['consts']['selected_row_field']: selected_row
                            }
                            self.logger.debug(
                                f"Marked Game: {game_key} in League: {league_name}, Selected Row: {selected_row}")
        except Exception as e:
            self.logger.warning(f"Error finding selected invest row: {e}")

    def find_first_total_in_table(self):
        self.logger.debug('searching for the first row in the total table')
        # Find all elements with class 'af3ed13'
        tables = self.driver.find_elements(By.CLASS_NAME, self.elements['consts']['total_table_class'])

        for table in tables:
            try:
                # Find the header inside the current 'af3ed13' element
                header = table.find_element(By.CLASS_NAME, self.elements['consts']['table_header_class'])
                header_text = header.find_element(By.CLASS_NAME,
                                                  self.elements['consts']['table_header_text_class']).text

                # Check if the header text is 'Total (incl. overtime)'
                if header_text == self.elements['consts']['table_text_value']:
                    # If the element does not have the 'show' class, click to expand it
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

                    # Check conditions
                    return {
                        self.elements['consts']['total_text_value']: expected_total_score,
                        self.elements['consts']['over_text_value']: over_value,
                        self.elements['consts']['under_text_value']: under_value
                    }
                    # If suitable rows are found, return the one with the smallest Under value
                return None
            except Exception as e:
                self.logger.warning(f"Error finding the Total table: {e}")
                continue

        return None

    def find_total_table(self, game_first_total_score):
        # Find all elements with class 'af3ed13'
        tables = self.driver.find_elements(By.CLASS_NAME, self.elements['consts']['total_table_class'])

        for table in tables:
            try:
                # Find the header inside the current 'af3ed13' element
                header = table.find_element(By.CLASS_NAME, self.elements['consts']['table_header_class'])
                header_text = header.find_element(By.CLASS_NAME,
                                                  self.elements['consts']['table_header_text_class']).text

                # Check if the header text is 'Total (incl. overtime)'
                if header_text == self.elements['consts']['table_text_value']:
                    # If the element does not have the 'show' class, click to expand it
                    if self.elements['consts']['show_text_value'] not in table.get_attribute('class'):
                        table.click()

                    # Extract suitable rows
                    suitable_rows = self.extract_suitable_rows(table, game_first_total_score)

                    # If suitable rows are found, return the one with the smallest Under value
                    if suitable_rows:
                        best_row = min(suitable_rows, key=lambda x: x[self.elements['consts']['under_text_value']])
                        return best_row
                    return None
            except Exception as e:
                self.logger.warning(f"Error finding the Total table: {e}")
                continue

        return None

    def extract_suitable_rows(self, total_table, game_first_total_score):
        suitable_rows = []

        # Locate all rows within the table
        rows = total_table.find_elements(By.CLASS_NAME, self.elements['consts']['table_rows_class'])

        for row in rows:
            expected_total_score = float(
                row.find_element(By.CLASS_NAME, self.elements['consts']['table_row_total_score_class']).text)
            over_value = float(
                row.find_elements(By.CLASS_NAME, self.elements['consts']['table_row_over_score_class'])[0].text)
            under_value = float(
                row.find_elements(By.CLASS_NAME, self.elements['consts']['table_row_under_score_class'])[1].text)

            # Check conditions
            if (expected_total_score >= game_first_total_score + self.point_difference) and (under_value >= 1.8):
                row_data = {
                    self.elements['consts']['total_text_value']: expected_total_score,
                    self.elements['consts']['over_text_value']: over_value,
                    self.elements['consts']['under_text_value']: under_value
                }
                suitable_rows.append(row_data)

        return suitable_rows
