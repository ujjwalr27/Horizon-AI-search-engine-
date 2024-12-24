import os
from dotenv import load_dotenv

load_dotenv()

# Core Configuration
SEARCH_KEY = os.getenv('GOOGLE_SEARCH_KEY')
SEARCH_ID = os.getenv('GOOGLE_SEARCH_ID')
SEARCH_URL = "https://www.googleapis.com/customsearch/v1?key={key}&cx={cx}&q={query}&start={start}&num=10"

# Database Configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Redis Configuration
# Redis Configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_USER = os.getenv('REDIS_USER', 'default')
REDIS_PASS = os.getenv('REDIS_PASS')
# Updated Redis URL format for internal connections
REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}"
REDIS_MAX_CONNECTIONS = 3
REDIS_TIMEOUT = 2

# Application Settings
MAX_SEARCH_RESULTS = 10
MAX_CONCURRENT_REQUESTS = 5
REQUEST_TIMEOUT = 5
CACHE_EXPIRY = 1800  # 30 minutes
MAX_CACHE_ENTRIES = 100
MAX_CACHE_SIZE = 50000  # ~50KB per entry

# Server Configuration
PORT = int(os.getenv('PORT', 5000))
WORKERS = 1
THREADS = 2

# Add to settings.py

# Relevance Settings
RELEVANCE_BOOST_FACTOR = 2.0  # Multiplier for relevant results
CLICK_COUNT_WEIGHT = 0.5  # Weight for click count in ranking
ML_RANK_WEIGHT = 0.3  # Weight for ML ranking in final score

# Time-based Settings
TIME_DECAY_FACTOR = 0.85  # Factor for time decay in ranking
MAX_RESULT_AGE_DAYS = 365  # Maximum age of results to consider
REFRESH_THRESHOLD_HOURS = 24  # Threshold to refresh cached results

# Cache Settings
CACHE_TIME_FILTERS = ['day', 'month', 'year']  # Available time filters