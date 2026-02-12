import os

# Base paths
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(ROOT_DIR, 'user_address_book')

# Persistent Storage Paths
JSON_STORAGE_PATH = os.path.join(DATA_DIR, 'contacts.json')
CSV_STORAGE_PATH = os.path.join(DATA_DIR, 'contacts.csv')
PICKLE_STORAGE_PATH = os.path.join(DATA_DIR, 'contacts.pkl')

# Feature Configuration
DEFAULT_BIRTHDAY_LOOKAHEAD_DAYS = 21

# UX Configuration
AUTO_HELP_THRESHOLD = 6
