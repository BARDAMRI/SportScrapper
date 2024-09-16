import json
import os
import logging
import sys
import certifi
from PlayManager import PlayManager
from logging.handlers import RotatingFileHandler
from pymongo import MongoClient
from PyQt5.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QThread
from GameWindow import GameWindow

config_path = os.path.join(os.getcwd(), 'assets', 'config.json')

print(f'os.cwd : {os.getcwd()}')
global logger, config, cluster_name, collection_name, client, db, collection, root, header, welcome_message, start_button, window, game_window, manager, thread

language = 'he'
language_button = '🇮🇱'
translations = {}


def init_configurations():
    global config, translations, config_path, game_window
    try:
        print(f'loading config file on path {config_path}')
        with open(config_path, 'r') as file:
            config = json.load(file)
            print("Configurations loaded successfully:", config)
            try:
                translations_path = os.path.join(os.getcwd(), 'assets', 'translations.json')
                with open(translations_path, 'r') as f:
                    translations = json.load(f)
            except FileNotFoundError as e:
                print(f"Error: translations.json file not found: {str(e)}")
                if game_window:
                    game_window.close_windows()
                sys.exit(1)
            except json.JSONDecodeError as e:
                print(f"Error: Invalid JSON in translations.json: {str(e)}")
                if game_window:
                    game_window.close_windows()
                sys.exit(1)
    except FileNotFoundError:
        print(f"Error: The configurations file '{translations_path}' was not found.")
    except json.JSONDecodeError:
        print(f"Error: The configurations file '{translations_path}' contains invalid JSON.")
    except Exception as e:
        print(f"An unexpected error occurred during configurations file loading: {e}")


def initialize_logger(log_level=logging.INFO, max_file_size=5 * 1024 * 1024, backup_count=5):
    global logger, config

    # Use a user-writable directory for logs
    if os.name == 'nt':  # For Windows, use AppData
        log_dir = os.path.join(os.getenv('APPDATA'), 'SportScrapper', 'logs')
    else:  # For Linux/Mac, use the home directory
        log_dir = os.path.join(os.getenv('HOME'), 'SportScrapper', 'logs')

    # Create the directory if it doesn't exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Determine log file name based on config or default to 'SportScrapperLogs.log'
    name = config.get("logger_file_name", 'SportScrapperLogs.log')
    log_file_path = os.path.join(log_dir, name)

    print(f'Loading log file on dir: {log_file_path}')
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)

    # Check if the logger already has handlers (to avoid duplicate logging)
    if not logger.handlers:
        console_handler = logging.StreamHandler()  # Logs to console
        file_handler = RotatingFileHandler(log_file_path, maxBytes=max_file_size,
                                           backupCount=backup_count)  # Logs to file
        console_handler.setLevel(log_level)
        file_handler.setLevel(log_level)

        # Define the log format
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        # Add the handlers to the logger
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    return logger


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
    except Exception as e:
        if logger:
            logger.warning(f'Connection to db failed: {e}')
        else:
            print(f'Connection to db failed: {e}')
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
    except Exception as e:
        if logger:
            logger.error(f"Error during access verification: {e}")
        else:
            print("Access denied. Exiting the program.")
        return False


def start_scrapping():
    global game_window, manager, thread

    # Create a QThread object
    thread = QThread()

    # Create the PlayManager instance
    manager = PlayManager(logger=logger, max_try_count=config['max_retry_number'], elements=config['elements'],
                          point_difference=config['point_difference'],
                          refreshTime=config['time_between_refreshes_in_sec'], game_window=game_window)
    manager.data_updated.connect(game_window.update_game_data)
    # Move the PlayManager instance to the QThread
    manager.moveToThread(thread)

    # Connect signals and slots
    thread.started.connect(manager.play)  # Start the PlayManager's play method when the thread starts
    manager.finished.connect(thread.quit)  # Quit the thread when PlayManager emits 'finished'
    manager.finished.connect(manager.deleteLater)  # Delete PlayManager after finishing
    thread.finished.connect(thread.deleteLater)  # Delete the thread when it's done

    # Start the thread
    thread.start()

    # Perform login
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
    logger.info("Window is closing")
    if thread.isRunning():
        manager.stop()  # Safely stop the PlayManager thread
        thread.quit()
        thread.wait()  # Ensure the thread is stopped before exiting
    sys.exit()


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

    except Exception as e:
        logger.error(f'Error on UI window open in open_welcome_window. Error : ${str(e)}')


def start_application():
    try:
        global game_window, logger, config, translations, language
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

    except Exception as e:
        logger.error(f'Failed to initialize the game.. Received error : ${str(e)}')
        if thread:
            thread.quit()
        if game_window:
            game_window.close_windows()
        sys.exit(1)


def start_program_and_play():
    open_welcome_window()


def open_ui():
    open_welcome_window()


if __name__ == '__main__':
    global cluster_name, collection_name, client, db, collection, config, thread, manager, logger, game_window
    try:
        try:
            init_configurations()
            initialize_logger()
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
                    start_program_and_play()
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
