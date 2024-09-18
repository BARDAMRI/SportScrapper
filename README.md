# Sport Scrapper Project

## Overview

This project monitors basketball games, scrapes game data, and updates the user in real-time. It uses Selenium for web
scraping, PyQt5 for the UI, and MongoDB for data storage. It supports multiple browsers (Chrome, Firefox, Edge, Safari).

## Setup

### Prerequisites

Ensure you have the following installed:

1. **Python 3.x**
2. **MongoDB**: A MongoDB instance where the game's data will be stored.
3. **WebDriver**: Browsers (Chrome, Firefox, Edge, Safari) need to have their respective WebDriver installed.
4. **PyQt5**: For the UI.
5. **Selenium**: For web scraping.

#### WebDriver Installation

- **Chrome**: Install ChromeDriver from [here](https://sites.google.com/a/chromium.org/chromedriver/).
- **Firefox**: Install GeckoDriver from [here](https://github.com/mozilla/geckodriver/releases).
- **Edge**: Install EdgeDriver from [here](https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/).
- **Safari**: Safari’s WebDriver is already installed on macOS but must be enabled using the following command:
  ```bash
  safaridriver --enable

## Configuration Files

### config.json

This file contains all the essential configurations required to run the project. Below is a description of each key.

```json5

{
  "logger_file_name": "SportScrapperLogs.log",
  "max_retry_number": 3,
  "point_difference": 5,
  "time_between_refreshes_in_sec": 30,
  "elements": {
    "consts": {
      "login_username_element_name": "username",
      "login_password_element_name": "password",
      "login_bottom_xpath": "//button[@id='loginButton']",
      "live_events_suffix": "/live",
      "basketball_section_container_xpath": "//div[@id='basketballSection']",
      "leagues_section_class": "league-section",
      "leagues_header_class": "league-header",
      "first_team_name_class": "team1-name",
      "second_team_name_class": "team2-name",
      "game_scores_pair_section": "scores",
      "quarter_number_class": "quarter",
      "time_left_class": "time-left",
      "collapsed_league_class": "collapsed",
      "table_text_value": "Total",
      "show_text_value": "show",
      "total_table_class": "total-table",
      "table_header_class": "table-header",
      "table_rows_class": "table-row",
      "min_under_value": 100.5,
      "over_text_value": "Over",
      "under_text_value": "Under",
      "curr_row_index": "row_index",
      "table_row_total_score_class": "total-score",
      "table_row_over_score_class": "over-score",
      "table_row_under_score_class": "under-score"
    }
  },
  "DB": {
    "cluster_name": "<your-cluster-name>",
    "db_name": "<your-db-name>",
    "db_username": "<your-username>",
    "db_password": "<your-password>",
    "collection_name": "<your-collection-name>",
    "connection_string": "mongodb+srv://{username}:{password}@{cluster}.mongodb.net/test?retryWrites=true&w=majority"
  },
  "url": "https://example.com",
  "basketball": "/basketball",
  "username": "<your-username>",
  "password": "<your-password>"
}
```

#### Configuration Parameters

	•	logger_file_name: Specifies the name of the log file.
	•	max_retry_number: The maximum number of retry attempts for actions (like loading the browser).
	•	point_difference: The threshold difference between points for tracking.
	•	time_between_refreshes_in_sec: Time between data refresh cycles (in seconds).
	•	elements: Contains all the required HTML elements used by Selenium for scraping the website.
	•	DB: Database credentials for connecting to a MongoDB instance.
	•	cluster_name: Name of the MongoDB cluster.
	•	db_name: Name of the database.
	•	db_username: Username for accessing the database.
	•	db_password: Password for accessing the database.
	•	collection_name: The collection name where the game data is stored.
	•	connection_string: MongoDB connection string, formatted with username and password.
	•	url: The URL of the website for scraping.
	•	basketball: URL path to the basketball section of the site.
	•	username: Login username for the site.
	•	password: Login password for the site.

### translations.json

This file holds the translations for different languages. The application currently supports English and Hebrew.

```json5
{
  "en": {
    "project_name": "Sport Scrapper",
    "welcome": "Welcome to Sport Scrapper",
    "start_analyze": "Start Analyze",
    "Leagues": "Leagues",
    "Marked Games": "Marked Games",
    "League Games": "League Games",
    "Game": "Game",
    "League": "League",
    "Current Score": "Current Score",
    "First Guessed Score": "First Guessed Score",
    "Selected Row Number": "Selected Row Number",
    "Selected Row total Score": "Selected Row Total Score",
    "Selected Row Under Score": "Selected Row Under Score",
    "Selected Row Over Score": "Selected Row Over Score"
  },
  "he": {
    "project_name": "ספורט סקרפר",
    "welcome": "ברוך הבא לספורט סקרפר",
    "start_analyze": "התחל לנתח",
    "Leagues": "ליגות",
    "Marked Games": "משחקים מסומנים",
    "League Games": "משחקי ליגה",
    "Game": "משחק",
    "League": "ליגה",
    "Current Score": "תוצאה נוכחית",
    "First Guessed Score": "ניחוש ראשון",
    "Selected Row Number": "מספר שורה נבחרת",
    "Selected Row total Score": "תוצאת שורה נבחרת",
    "Selected Row Under Score": "ניקוד מתחת נבחר",
    "Selected Row Over Score": "ניקוד מעל נבחר"
  }
}
```

#### Translation Keys

	•	project_name: The title of the application.
	•	welcome: Welcome message on the main screen.
	•	start_analyze: Text for the button that starts the analysis.
	•	Other keys: Labels for UI components such as “Leagues,” “Marked Games,” and game-related data.

## Running the Program

1. Install Dependencies

Run the following command to install required Python packages:

```bash
pip install -r requirements.txt
```

2. Configure the Project:

Ensure you have set the correct values in the config.json file and the translations.json file.

3. Run the Program:

You can launch the application by executing the main Python file:

```bash
python src/main.py
```

## Browser Setup

The application uses Selenium WebDriver to interact with the web page. Ensure you have the correct WebDriver installed and configured for the browser you are using.

For Safari (macOS), use the following command to enable the WebDriver:
```bash
safaridriver --enable
```

For Chrome, Firefox, and Edge, ensure the WebDriver is installed and available in your system’s PATH, or modify the retry_driver method in the code to set the WebDriver path correctly.

This guide provides a complete overview of how to set up and run the Sport Scrapper project.

You can copy and paste this content into your `README.md` file. It includes all the necessary configurations and setup details for your project.