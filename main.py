import json
import os
import logging
from pagesCoppier import Coppier
from playManager import playManager
from logging.handlers import RotatingFileHandler

config_file = 'config.json'
config_path = os.path.join(os.path.dirname(__file__), config_file)

try:
    with open(config_path, 'r') as file:
        config = json.load(file)
        print("Configurations loaded successfully:", config)
        # You can use the configuration as needed here
except FileNotFoundError:
    print(f"Error: The configuration file '{config_file}' was not found.")
except json.JSONDecodeError:
    print(f"Error: The configuration file '{config_file}' contains invalid JSON.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")


def copyPages():
    copy = Coppier(config['url'], config['basketball'], config['username'], config['password'])
    copy.save_webpage()


def initialize_logger(log_file_name="sportsScrapper.log", log_level=logging.INFO, max_file_size=5 * 1024 * 1024, backup_count=5):
    """
    Initialize the logger with a rotating file handler.

    :param log_file_name: Name of the log file.
    :param log_level: Logging level.
    :param max_file_size: Maximum size of the log file in bytes before rotating.
    :param backup_count: Number of backup files to keep.
    :return: Configured logger instance.
    """
    # Create a custom logger
    logger = logging.getLogger(__name__)

    # Set the log level
    logger.setLevel(log_level)

    # Create handlers
    console_handler = logging.StreamHandler()
    file_handler = RotatingFileHandler(log_file_name, maxBytes=max_file_size, backupCount=backup_count)
    console_handler.setLevel(log_level)
    file_handler.setLevel(log_level)

    # Create formatters and add them to handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # Add handlers to the logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)


# Initialize the logger
logger = initialize_logger()


def play():
    manager = playManager(logger, config['elements'], config['point_difference'],
                          config['time_between_refreshes_in_sec'])
    init_succeeded = manager.login(config['url'], config['basketball'], config['username'], config['password'])
    if init_succeeded:
        manager.play()
    else:
        print('Could not initialize the game. An error occurred during launching the games main page.')
        logger.info('Could not initialize the game. An error occurred during launching the games main page.')


if config and config['url'] and config['username'] and config['password']:
    # Login and invest
    # copyPages()
    initialize_logger()
    play()
