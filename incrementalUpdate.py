from pymongo import MongoClient
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# Configuration from environment variables
MONGO_USER = os.getenv('MONGO_USER')
MONGO_PASSWORD = os.getenv('MONGO_PASSWORD')
MONGO_CLUSTER = os.getenv('MONGO_CLUSTER')
DB_NAME = os.getenv('MONGO_DB_NAME')
COLLECTION_NAME = os.getenv('MONGO_COLLECTION_NAME')

# Updated connection string using data from the .env file
MONGO_CONNECTION_STRING = f"mongodb+srv://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_CLUSTER}/?retryWrites=true&w=majority&appName=Barcelona"

# Connect to MongoDB
client = MongoClient(MONGO_CONNECTION_STRING)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

def get_businesses_to_update(hours_threshold=24):
    """Get businesses that haven't been updated in the specified hours"""
    threshold_time = datetime.now() - timedelta(hours=hours_threshold)
    query = {
        '$or': [
            {'last_updated': {'$lt': threshold_time.isoformat()}},
            {'last_updated': {'$exists': False}}
        ]
    }
    return list(collection.find(query))

# Example usage
if __name__ == "__main__":
    businesses_to_update = get_businesses_to_update()
    print(f"Businesses to update: {len(businesses_to_update)}") 