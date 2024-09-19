import json
import time
import certifi
from selenium.common import WebDriverException
import logging
import os
import stat
import sys
from PlayManager import PlayManager
from logging.handlers import RotatingFileHandler
from pymongo import MongoClient
from PyQt5.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QThread
from GameWindow import GameWindow
import platform
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.safari.webdriver import WebDriver as SafariDriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium import webdriver

config_path = os.path.join(os.getcwd(), 'assets', 'config.json')
trans_path = os.path.join(os.getcwd(), 'assets', 'translations.json')

print(f'os.cwd : {os.getcwd()}')
logger = None
config = None
cluster_name = None
collection_name = None
client = None
db = None
collection = None
root = None
header = None
welcome_message = None
start_button = None
window = None
game_window = None
manager = None
language = 'he'
language_button = '🇮🇱'
translations = {}
system_type = platform.system()  # Store system type
driver = None
chrome_options = ChromeOptions()
firefox_options = FirefoxOptions()
edge_options = EdgeOptions()
thread = None


def init_configurations():
    global config, translations, config_path, trans_path, game_window, logger
    try:
        logger.info(f'loading config file on path {config_path} and translations on path {trans_path}')
        with open(config_path, 'r', encoding='utf-8') as file:
            config = json.load(file)
            print("Configurations loaded successfully:", config)
            try:
                with open(trans_path, 'r', encoding='utf-8') as f:
                    translations = json.load(f)
                    print(f'Translations: {translations}')
            except FileNotFoundError as err:
                print(f"Error: translations.json file not found: {str(err)}")
                if game_window:
                    game_window.close_windows()
                sys.exit(1)
            except json.JSONDecodeError as err:
                print(f"Error: Invalid JSON in translations.json: {str(err)}")
                if game_window:
                    game_window.close_windows()
                sys.exit(1)
    except FileNotFoundError:
        print(f"Error: The configurations file '{trans_path}' was not found.")
    except json.JSONDecodeError:
        print(f"Error: The configurations file '{trans_path}' contains invalid JSON.")
    except Exception as err:
        print(f"An unexpected error occurred during configurations file loading: {err}")


def initialize_logger(log_level=logging.INFO, max_file_size=5 * 1024 * 1024, backup_count=5):
    global logger, config

    try:
        # Use a user-writable directory for logs
        if os.name == 'nt':  # For Windows, use AppData
            log_dir = os.path.join(os.getenv('APPDATA'), 'SportScrapper', 'logs')
        else:  # For Linux/Mac, use the home directory
            log_dir = os.path.join(os.getenv('HOME'), 'SportScrapper', 'logs')

        # Create the directory if it doesn't exist
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # Determine log file name based on config or default to 'SportScrapperLogs.log'
        name =  'SportScrapperLogs.log'
        log_file_path = os.path.join(log_dir, name)

        print(f'Attempting to load log file at: {log_file_path}')
        logger = logging.getLogger(__name__)
        logger.setLevel(log_level)

        # Check if the logger already has handlers (to avoid duplicate logging)
        if not logger.handlers:
            console_handler = logging.StreamHandler()  # Logs to console
            console_handler.setLevel(log_level)

            # Try opening the log file, or create a new one if it's inaccessible or too large
            file_handler = get_file_handler(log_file_path, max_file_size, backup_count)
            file_handler.setLevel(log_level)

            # Define the log format
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            file_handler.setFormatter(formatter)

            # Add the handlers to the logger
            logger.addHandler(console_handler)
            logger.addHandler(file_handler)

    except Exception as e:
        print(f"Failed to initialize logger: {e}")
        sys.exit(1)


def get_file_handler(log_file_path, max_file_size, backup_count):
    """
    Tries to create a RotatingFileHandler. If the file is inaccessible, delete it and create a new one.
    """
    try:
        # Check if the file exists and its size
        if os.path.exists(log_file_path):
            if os.access(log_file_path, os.W_OK):  # Check if we have write permission
                if os.path.getsize(log_file_path) >= max_file_size:
                    print(f"Log file {log_file_path} reached max size, rotating...")
            else:
                print(f"Log file {log_file_path} is inaccessible, deleting and recreating...")
                os.remove(log_file_path)  # Delete the inaccessible file
                create_new_log_file(log_file_path)
        else:
            create_new_log_file(log_file_path)

        # Create a RotatingFileHandler that automatically rotates the log file
        return RotatingFileHandler(log_file_path, maxBytes=max_file_size, backupCount=backup_count)

    except (IOError, OSError) as e:
        print(f"Failed to create or access log file {log_file_path}: {str(e)}")
        sys.exit(1)


def create_new_log_file(log_file_path):
    """
    Creates a new log file and grants full permissions to the file.
    """
    try:
        with open(log_file_path, 'w') as new_log_file:
            new_log_file.write('')  # Create an empty file
        # Set permissions: read, write, and execute for everyone (777)
        os.chmod(log_file_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)  # Set file permissions to 777
        print(f"New log file {log_file_path} created with full permissions.")

    except Exception as e:
        print(f"Failed to create new log file: {e}")
        sys.exit(1)


def initDB():
    global cluster_name, collection_name, client, db, collection, logger, game_window
    cluster_name = config['DB']['cluster_name']
    db_name = config['DB']['db_name']
    username = config['DB']['db_username']
    password = config['DB']['db_password']
    collection_name = config['DB']['collection_name']
    connection_string = config['DB']['connection_string']
    connection_string = connection_string.format(username=username, password=password, cluster=cluster_name)
    client = MongoClient(connection_string, tlsCAFile=certifi.where())
    try:
        client.admin.command('ping')
        if logger:
            logger.info('Connection to db succeeded.')
        else:
            print('Connection to db succeeded.')
    except Exception as err:
        if logger:
            logger.warning(f'Connection to db failed: {err}')
        else:
            print(f'Connection to db failed: {err}')
        if game_window:
            game_window.close_windows()
        sys.exit(1)
    db = client[db_name]
    collection = db[collection_name]


def verify_access():
    global collection, logger
    try:
        # Fetch the access control document
        access_document = collection.find_one()
        if access_document and access_document.get('access_allowed', False):
            if logger:
                logger.info('Access granted to program. Launching the application...')
            else:
                print('Access granted to program. Launching the application...')
            return True
        else:
            if logger:
                logger.warning("Access denied. Exiting the program.")
            else:
                print("Access denied. Exiting the program.")
            return False
    except Exception as err:
        if logger:
            logger.error(f"Error during access verification: {err}")
        else:
            print("Access denied. Exiting the program.")
        return False


def configure_options():
    global chrome_options, firefox_options, edge_options
    """Configure browser options for headless mode and other flags."""
    for options in [chrome_options, firefox_options, edge_options]:
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-software-rasterizer")


def retry_driver():
    global driver, system_type, logger

    max_attempts = config['max_retry_number']
    """Retries launching the WebDriver up to max_attempts in case of failure."""
    attempt_count = 0

    while not driver and attempt_count < max_attempts:
        try:
            # Load the appropriate WebDriver based on the system type
            if system_type == 'Windows':
                driver = load_chrome() or load_edge() or load_firefox()
            elif system_type == 'Linux':
                driver = load_chrome() or load_firefox()
            elif system_type == 'Darwin':  # macOS
                driver = load_chrome() or load_safari() or load_firefox()

            if driver:
                logger.info(f"{system_type} WebDriver successfully launched.")
                return True
        except (WebDriverException, Exception) as err:
            logger.error(
                f"WebDriver failed to launch: {str(err)}. Attempt {attempt_count + 1} of {max_attempts}.")
            attempt_count += 1

    logger.critical("Failed to launch WebDriver after several attempts. Exiting program.")
    return False


def load_chrome():
    global logger, chrome_options
    """Attempts to load the Chrome WebDriver."""
    try:
        logger.info("Attempting to launch Chrome WebDriver...")
        service = webdriver.ChromeService()
        return webdriver.Chrome(service=service, options=chrome_options)
    except WebDriverException as err:
        logger.error(f"Chrome WebDriver failed: {str(err)}")
        return None


def load_firefox():
    global logger, firefox_options
    """Attempts to load the Firefox WebDriver."""
    try:
        logger.info("Attempting to launch Firefox WebDriver...")
        return webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()),
                                 options=firefox_options)
    except WebDriverException as err:
        logger.error(f"Firefox WebDriver failed: {str(err)}")
        return None


def load_edge():
    global system_type, logger, edge_options
    """Attempts to load the Edge WebDriver on Windows."""
    if system_type == 'Windows':
        try:
            logger.info("Attempting to launch Edge WebDriver...")
            return webdriver.Edge(service=EdgeService(EdgeChromiumDriverManager().install()),
                                  options=edge_options)
        except WebDriverException as err:
            logger.error(f"Edge WebDriver failed: {str(err)}")
            return None


def load_safari():
    global logger, system_type
    """Attempts to load the Safari WebDriver on macOS."""
    if system_type == 'Darwin':
        try:
            logger.info("Attempting to launch Safari WebDriver...")
            return SafariDriver()
        except WebDriverException as err:
            logger.error(f"Safari WebDriver failed: {str(err)}")
            return None


def on_game_window_closed():
    global driver, thread
    logger.info("Game window closed. Cleaning up resources...")
    manager.stop()
    if driver:
        driver.quit()


def start_scrapping():
    global game_window, manager, thread, driver
    if thread and thread.isRunning():
        thread.quit()
        thread.wait()
    thread = QThread()
    configure_options()

    # Create driver with retry logic
    driver = None
    if not retry_driver():
        raise Exception('Failed to load the Web Driver. Exiting...')

    # Create the PlayManager instance
    manager = PlayManager(driver=driver, logger=logger, max_try_count=config['max_retry_number'],
                          elements=config['elements'],
                          point_difference=config['point_difference'],
                          refreshTime=config['time_between_refreshes_in_sec'], game_window=game_window)
    manager.data_updated.connect(game_window.update_game_data)
    game_window.window_closed.connect(on_game_window_closed)
    manager.moveToThread(thread)

    thread.started.connect(manager.play)
    manager.finished.connect(thread.quit)
    manager.finished.connect(thread.deleteLater)
    thread.finished.connect(thread.deleteLater)

    thread.start()

    # Perform login and start
    init_succeeded = manager.login(config['url'], config['basketball'], config['username'], config['password'])

    if init_succeeded and thread:
        logger.info('The game manager was initialized successfully...')
        QApplication.processEvents()
    else:
        logger.info('Could not initialize the game. An error occurred during launching the games main page...')
        thread.quit()
        sys.exit(1)


def select_language():
    global language
    if language == 'he':
        language = 'en'
    else:
        language = 'he'
    update_ui_language()


def update_ui_language():
    global game_window, language, translations, language_button, start_button, welcome_message, header
    header.setText(translations[language]["project_name"])
    welcome_message.setText(translations[language]["welcome"])
    start_button.setText(translations[language]["start_analyze"])
    language_button.setText("🇺🇸" if language == 'he' else "🇮🇱")
    if game_window:
        game_window.update_translation(translations[language])


def on_closing():
    global driver, logger, thread, manager
    try:
        logger.info("Closing program...")

        if manager:  # Ensure the PlayManager stops its work
            logger.info("Stopping PlayManager...")
            manager.stop_flag = True  # Set the stop flag to True

        if thread and thread.isRunning():
            logger.info("Stopping thread...")
            thread.quit()  # This stops the thread's event loop
            thread.wait()  # Wait for the thread to finish

        if driver:
            logger.info("Closing driver...")
            driver.quit()

        logger.info("Exiting application...")
        sys.exit(0)
    except Exception as err:
        logger.error(f'Failed to close program peacefully. Error : {err}')
        sys.exit(1)


def open_welcome_window():
    global header, welcome_message, start_button, language, translations, window, language_button


    try:
        app = QApplication(sys.argv)

        # Create the main window
        window = QWidget()
        window.setWindowTitle("Sport Scrapper")
        window.setFixedSize(800, 600)

        # Load and set the background image
        bg_label = QLabel(window)
        bg_pixmap = QPixmap(os.path.join(os.getcwd(), 'assets', 'entrancePageImage.png'))
        bg_label.setPixmap(bg_pixmap)
        bg_label.setScaledContents(True)
        bg_label.resize(window.size())

        # Top layout for headers
        top_layout = QVBoxLayout()
        top_layout.setAlignment(Qt.AlignTop)
        top_layout.setContentsMargins(0, 20, 0, 0)  # Adjust margins to top

        # Header label
        header = QLabel(translations[language]["project_name"])
        header.setStyleSheet("font-size: 36px; font-weight: bold; color: white;")
        header.setAlignment(Qt.AlignCenter)
        top_layout.addWidget(header)

        # Welcome message
        welcome_message = QLabel(translations[language]["welcome"])
        welcome_message.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        welcome_message.setAlignment(Qt.AlignCenter)
        top_layout.addWidget(welcome_message)

        # Overlay layout for central content
        central_layout = QVBoxLayout()
        central_layout.setAlignment(Qt.AlignCenter)
        central_layout.setContentsMargins(0, 150, 0, 50)  # Adjust margins to center the content

        # Start Analyze button
        start_button = QPushButton(translations[language]["start_analyze"])
        start_button.setStyleSheet("""
            font-size: 22px;
            font-weight: 900;
            background-color: white;
            padding: 10px 20px;
            border-radius: 15px;
            """)
        start_button.clicked.connect(start_application)
        central_layout.addWidget(start_button)

        # Create a container widget for top content
        top_widget = QWidget(window)
        top_widget.setLayout(top_layout)
        top_widget.setAttribute(Qt.WA_TranslucentBackground)  # Make the background transparent
        top_widget.resize(window.size())
        top_widget.move(0, 0)

        # Create a container widget for central content
        central_widget = QWidget(window)
        central_widget.setLayout(central_layout)
        central_widget.setAttribute(Qt.WA_TranslucentBackground)  # Make the background transparent
        central_widget.resize(window.size())
        central_widget.move(0, 0)

        # Language button (flags as text)
        language_button = QPushButton("🇺🇸" if language == 'he' else "🇮🇱", window)
        language_button.setStyleSheet("font-size: 18px; background-color: transparent; color: white;")
        language_button.clicked.connect(select_language)
        language_button.resize(100, 40)
        language_button.move(window.width() - 110, 10)

        # Handle window close event
        app.aboutToQuit.connect(on_closing)

        # Show the window
        window.show()

        sys.exit(app.exec_())

    except Exception as err:
        logger.error(f'Error on UI window open in open_welcome_window. Error : {str(err)}')
        print(f'Error on UI window open in open_welcome_window. Error : {str(err)}')
        time.sleep(5)


def start_application():
    global game_window, logger, config, translations, language, thread
    try:

        # Create and display the game window immediately after access verification
        game_window = GameWindow(logger=logger, elements=config['elements'], translation=translations[language])
        game_window.show()
        QApplication.processEvents()  # Force the window to display immediately

        if verify_access():
            start_scrapping()
        else:
            logger.warning("Access Denied, You do not have permission to run this software.")
            if game_window:
                game_window.close_windows()
            sys.exit(1)  # Ensure the program exits if access is denied

    except Exception as err:
        logger.error(f'Failed to initialize the game.. Received error : ${str(err)}')
        if thread:
            thread.quit()
            thread.wait()
        sys.exit(1)


if __name__ == '__main__':
    try:
        try:
            initialize_logger()
            init_configurations()
            if logger:
                logger.info('Configurations file and translation were loaded successfully!')
            else:
                print('Configurations file and translation were loaded successfully! But logger wasn\'t found')
            initDB()
        except Exception as e:
            if logger:
                logger.error(f'Failed to load system resources. Error : ${str(e)}')
            else:
                print(f'Failed to load system resources. Error : ${str(e)}')
            if game_window:
                game_window.close_windows()
            sys.exit(1)
        try:
            if config and config['url'] and config['username'] and config['password']:
                if verify_access():
                    open_welcome_window()
                else:
                    if game_window:
                        game_window.close_windows()
                    sys.exit(1)
        except Exception as e:
            if logger:
                logger.error(f'Received an error during system operation : ${str(e)}')
            else:
                print(f'Received an error during system operation : ${str(e)}')
            if game_window:
                game_window.close_windows()
            sys.exit(1)
    except Exception as e:
        if logger:
            logger.error(f'Failed to start the system. Error : ${str(e)}')
        else:
            print(f'Failed to start the system. Error : ${str(e)}')
        if game_window:
            game_window.close_windows()
        sys.exit(1)
