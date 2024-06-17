import json
import os

from pagesCoppier import Coppier
from playManager import playManager

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


def play():
    manager = playManager()
    manager.login(config['url'], config['basketball'], config['username'], config['password'])
    manager.play()


if config and config['url'] and config['username'] and config['password']:
    # Login and invest
    # copyPages()
    play()
