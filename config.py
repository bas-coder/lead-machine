import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")

# Scraping Settings
DEFAULT_DELAY = 0.15
MAX_RETRIES = 3
TIMEOUT = 10

# Output Settings
EXPORT_DIR = "exports"
LOG_DIR = "logs"
DATA_DIR = "data"

# Create directories if they don't exist
for directory in [EXPORT_DIR, LOG_DIR, DATA_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)
