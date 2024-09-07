import json
import os
import logging
import sys
import certifi
from pagesCoppier import Coppier
from PlayManager import PlayManager
from logging.handlers import RotatingFileHandler
from pymongo import MongoClient
from PyQt5.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt
from GameWindow import GameWindow

config_file = 'config.json'
config_path = os.path.join(os.path.dirname(__file__), config_file)
global logger, config, cluster_name, collection_name, client, db, collection, root, header, welcome_message, start_button, window, game_window

language = 'he'
language_button = '🇮🇱'
translations = {}


def initialize_logger(log_file_name="SportScrapperLogs.log", log_level=logging.INFO, max_file_size=5 * 1024 * 1024,
                      backup_count=5):
    global logger
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)

    # Check if the logger already has handlers (to avoid duplicate logging)
    if not logger.handlers:
        console_handler = logging.StreamHandler()
        file_handler = RotatingFileHandler(log_file_name, maxBytes=max_file_size, backupCount=backup_count)
        console_handler.setLevel(log_level)
        file_handler.setLevel(log_level)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    return logger


def init_configurations():
    global config, translations
    try:
        with open(config_path, 'r') as file:
            config = json.load(file)
            logger.info("Configurations loaded successfully:", config)
            try:
                with open('translations.json', 'r') as f:
                    translations = json.load(f)
            except FileNotFoundError:
                logger.error("Error: translations.json file not found.")
                sys.exit(1)
            except json.JSONDecodeError:
                logger.error("Error: Invalid JSON in translations.json.")
                sys.exit(1)
    except FileNotFoundError:
        logger.info(f"Error: The configuration file '{config_file}' was not found.")
    except json.JSONDecodeError:
        logger.info(f"Error: The configuration file '{config_file}' contains invalid JSON.")
    except Exception as e:
        logger.info(f"An unexpected error occurred: {e}")


def initDB():
    global cluster_name, collection_name, client, db, collection
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
        logger.info('Connection to db succeeded.')
    except Exception as e:
        logger.warning(f'Connection to db failed: {e}')
        sys.exit(1)
    db = client[db_name]
    collection = db[collection_name]


def verify_access():
    global collection
    try:
        # Fetch the access control document
        access_document = collection.find_one()
        if access_document and access_document.get('access_allowed', False):
            logger.info('Access granted to program. Launching the application...')
            return True
        else:
            logger.warning("Access denied. Exiting the program.")
            return False
    except Exception as e:
        print(f"Error during access verification: {e}")
        return False


def copyPages():
    copy = Coppier(config['url'], config['basketball'], config['username'], config['password'])
    copy.save_webpage()


def start_scrapping():
    global game_window
    manager = PlayManager(logger, config['elements'], config['point_difference'],
                          config['time_between_refreshes_in_sec'], game_window)
    init_succeeded = manager.login(config['url'], config['basketball'], config['username'], config['password'])

    if init_succeeded:
        logger.info('The game manager was initialized successfully...')
        QApplication.processEvents()
        manager.play()  # Start the game loop, which updates the game window dynamically
    else:
        logger.info('Could not initialize the game. An error occurred during launching the games main page...')


def select_language():
    global language
    if language == 'he':
        language = 'en'
    else:
        language = 'he'
    update_ui_language()


def update_ui_language():
    header.setText(translations[language]["project_name"])
    welcome_message.setText(translations[language]["welcome"])
    start_button.setText(translations[language]["start_analyze"])
    language_button.setText("🇺🇸" if language == 'he' else "🇮🇱")


def on_closing():
    print("Window is closing")
    sys.exit()


def open_welcome_window():
    global header, welcome_message, start_button, language, translations, window, language_button

    app = QApplication(sys.argv)

    # Create the main window
    window = QWidget()
    window.setWindowTitle("Sport Scrapper")
    window.setFixedSize(800, 600)

    # Load and set the background image
    bg_label = QLabel(window)
    bg_pixmap = QPixmap("/Users/bardamri/PycharmProjects/SportScrapper/entrancePageImage.png")
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


def start_application():
    global game_window
    # Create and display the game window immediately after access verification
    game_window = GameWindow()
    game_window.show()
    QApplication.processEvents()  # Force the window to display immediately

    if verify_access():
        start_scrapping()
    else:
        logger.warning("Access Denied, You do not have permission to run this software.")
        sys.exit(1)  # Ensure the program exits if access is denied


def start_program_and_play():
    open_welcome_window()


def open_ui():
    open_welcome_window()


if __name__ == '__main__':
    global cluster_name, collection_name, client, db, collection, config
    initialize_logger()
    init_configurations()
    initDB()
    if config and config['url'] and config['username'] and config['password']:
        if verify_access():
            start_program_and_play()
        else:
            sys.exit(1)
