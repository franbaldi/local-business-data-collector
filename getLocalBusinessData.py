import requests
import pymongo
import time
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
from ratelimit import limits, sleep_and_retry
from tqdm import tqdm

# Load environment variables
load_dotenv()

# Configuration from environment variables
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
MONGO_USER = os.getenv('MONGO_USER')
MONGO_PASSWORD = os.getenv('MONGO_PASSWORD')
MONGO_CLUSTER = os.getenv('MONGO_CLUSTER')  # Ensure this is your full cluster hostname, e.g., "cluster0.mongodb.net"
DB_NAME = os.getenv('MONGO_DB_NAME')
COLLECTION_NAME = os.getenv('MONGO_COLLECTION_NAME')

# Barcelona geographic bounds
BARCELONA_BOUNDS = {
    'southwest': {'lat': 41.320004, 'lng': 2.070932},
    'northeast': {'lat': 41.469576, 'lng': 2.228208}
}

# Rate limiting constants
CALLS_PER_DAY = 1000  # Free tier limit
SECONDS_PER_DAY = 24 * 60 * 60
CALLS_PER_SECOND = CALLS_PER_DAY / SECONDS_PER_DAY
MIN_TIME_BETWEEN_CALLS = 2  # Minimum seconds between API calls

# Updated connection string using data from the .env file
# Use "mongodb+srv://" for MongoDB Atlas connections.
MONGO_CONNECTION_STRING = f"mongodb+srv://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_CLUSTER}/?retryWrites=true&w=majority&appName=Barcelona"

# Or if you're running MongoDB locally without authentication
# MONGO_CONNECTION_STRING = 'mongodb://localhost:27017'

# Connect to MongoDB
client = MongoClient(MONGO_CONNECTION_STRING)
try:
    # Verify the connection
    client.admin.command('ping')
    print("Successfully connected to MongoDB!")
except Exception as e:
    print(f"Failed to connect to MongoDB: {e}")
    print(f"Connection string used: {MONGO_CONNECTION_STRING}")
    exit(1)

db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# Add this after load_dotenv()
print("MongoDB Configuration:")
print(f"MONGO_USER: {MONGO_USER}")
print(f"MONGO_CLUSTER: {MONGO_CLUSTER}")
print(f"DB_NAME: {DB_NAME}")
print(f"COLLECTION_NAME: {COLLECTION_NAME}")

@sleep_and_retry
@limits(calls=CALLS_PER_DAY, period=SECONDS_PER_DAY)
def get_google_places_data(query, api_key, page_token=None):
    base_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        'query': query,
        'key': api_key,
        'region': 'es',
        'language': 'en',
        'location': f"{(BARCELONA_BOUNDS['northeast']['lat'] + BARCELONA_BOUNDS['southwest']['lat'])/2},"
                   f"{(BARCELONA_BOUNDS['northeast']['lng'] + BARCELONA_BOUNDS['southwest']['lng'])/2}",
        'bounds': f"{BARCELONA_BOUNDS['southwest']['lat']},{BARCELONA_BOUNDS['southwest']['lng']}|"
                 f"{BARCELONA_BOUNDS['northeast']['lat']},{BARCELONA_BOUNDS['northeast']['lng']}"
    }
    
    if page_token:
        params['pagetoken'] = page_token
    
    response = requests.get(base_url, params=params)
    return response.json()

@sleep_and_retry
@limits(calls=CALLS_PER_DAY, period=SECONDS_PER_DAY)
def get_place_details(place_id, api_key):
    details_url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        'place_id': place_id,
        'key': api_key,
        'fields': 'name,formatted_address,rating,reviews,types,price_level,international_phone_number,website',
        'language': 'en'
    }
    
    response = requests.get(details_url, params=params)
    return response.json().get('result', {})

def process_business_data(place):
    time.sleep(MIN_TIME_BETWEEN_CALLS)  # Ensure minimum delay between API calls
    place_details = get_place_details(place['place_id'], GOOGLE_API_KEY)
    
    business_data = {
        'name': place_details.get('name'),
        'address': place_details.get('formatted_address'),
        'rating': place_details.get('rating'),
        'reviews': [review.get('text') for review in place_details.get('reviews', [])],
        'types': place_details.get('types', []),
        'price_level': place_details.get('price_level'),
        'phone': place_details.get('international_phone_number'),
        'website': place_details.get('website'),
        'google_maps_id': place['place_id'],
        'last_updated': datetime.now().isoformat()
    }
    
    return business_data

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

def main():
    # Search queries focused on real estate maintenance and services in Barcelona
    search_queries = [
        "plumbers Barcelona",
        "fontaneros Barcelona",
        "electricians Barcelona",
        "electricistas Barcelona",
        "home repair services Barcelona",
        "servicios mantenimiento hogar Barcelona",
        "cleaning services Barcelona",
        "servicios limpieza Barcelona",
        "HVAC maintenance Barcelona",
        "aire acondicionado mantenimiento Barcelona",
        "property maintenance Barcelona",
        "mantenimiento inmuebles Barcelona",
        "handyman services Barcelona",
        "servicios manitas Barcelona",
        "locksmith Barcelona",
        "cerrajeros Barcelona",
        "pest control Barcelona",
        "control plagas Barcelona",
        "painting services Barcelona",
        "pintores Barcelona",
        "carpentry services Barcelona",
        "carpinteros Barcelona",
        "renovation contractors Barcelona",
        "contractors reformas Barcelona",
        "window repair Barcelona",
        "reparación ventanas Barcelona",
        "appliance repair Barcelona",
        "reparación electrodomésticos Barcelona"
    ]
    
    # Create progress bar for search queries
    with tqdm(total=len(search_queries), desc="Processing search queries", unit="query") as pbar_queries:
        for query in search_queries:
            print(f"\nProcessing query: {query}")
            next_page_token = None
            places_processed = 0
            
            # Initialize progress bar for places (we'll update total when we get first response)
            places_pbar = tqdm(desc="Processing places", unit="place")
            
            while True:
                response_data = get_google_places_data(query, GOOGLE_API_KEY, next_page_token)
                places = response_data.get('results', [])
                
                # Update total on first iteration
                if places_processed == 0:
                    places_pbar.total = len(places)
                    places_pbar.refresh()
                
                for place in places:
                    business_data = process_business_data(place)
                    
                    # Update or insert document in MongoDB
                    collection.update_one(
                        {'google_maps_id': business_data['google_maps_id']},
                        {'$set': business_data},
                        upsert=True
                    )
                    places_pbar.set_postfix_str(f"Current: {business_data['name']}")
                    places_pbar.update(1)
                    places_processed += 1
                
                next_page_token = response_data.get('next_page_token')
                if not next_page_token:
                    break
                
                # Wait before requesting next page (Google API requirement)
                time.sleep(MIN_TIME_BETWEEN_CALLS)
            
            places_pbar.close()
            pbar_queries.update(1)

if __name__ == "__main__":
    main()