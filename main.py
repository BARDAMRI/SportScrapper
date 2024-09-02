import json
import os
import logging
import sys
import certifi
from pagesCoppier import Coppier
from playManager import playManager
from logging.handlers import RotatingFileHandler
from pymongo import MongoClient

config_file = 'config.json'
config_path = os.path.join(os.path.dirname(__file__), config_file)
global logger, config, cluster_name, collection_name, client, db, collection


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
    global config
    try:
        with open(config_path, 'r') as file:
            config = json.load(file)
            logger.info("Configurations loaded successfully:", config)
            # You can use the configuration as needed here
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
        print('Connection to db succeeded.')
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
    manager = playManager(logger, config['elements'], config['point_difference'],
                          config['time_between_refreshes_in_sec'])
    init_succeeded = manager.login(config['url'], config['basketball'], config['username'], config['password'])
    if init_succeeded:
        logger.info('The game manager was initialized successfully...')
        manager.play()
    else:
        logger.info('Could not initialize the game. An error occurred during launching the games main page...')


def open_ui():
    logger.info('Opening UI window...')
    # Proceed to open the UI and start the game duration
    # Example: self.launch_ui()
    # TODO: COMPLETE UI.


def start_program_and_play():
    global logger
    open_ui()
    start_scrapping()


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
