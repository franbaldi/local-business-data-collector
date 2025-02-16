# Local Business Data Collector

This project is designed to collect and update local business data for Barcelona using the Google Places API and store it in a MongoDB database. The project is divided into two main components: fetching complete business data and performing incremental updates.

## Project Structure

- **getLocalBusinessData.py**: This script fetches the complete list of businesses based on predefined search queries and stores the data in MongoDB.
- **incrementalUpdate.py**: This script identifies businesses that need to be updated based on a specified time threshold and updates their information in MongoDB.

## Prerequisites

- Python 3.x
- MongoDB (local or hosted, e.g., MongoDB Atlas)
- Google Places API Key

## Setup

1. **Clone the repository:**

   ```bash
   git clone https://github.com/franbaldi/local-business-data-collector.git
   cd local-business-data-collector
   ```

2. **Install dependencies:**

   Use `pip` to install the required Python packages:

   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Variables:**

   Create a `.env` file in the project root directory and add the following environment variables:

   ```plaintext
   GOOGLE_API_KEY=your_google_api_key
   MONGO_USER=your_mongo_user
   MONGO_PASSWORD=your_mongo_password
   MONGO_CLUSTER=your_mongo_cluster_hostname
   MONGO_DB_NAME=your_database_name
   MONGO_COLLECTION_NAME=your_collection_name
   ```

   Replace the placeholders with your actual credentials and configuration.

## Usage

### Fetch Complete Business Data

Run the `getLocalBusinessData.py` script to fetch and store the complete list of businesses:

```bash
python getLocalBusinessData.py
```

### Perform Incremental Updates

Run the `incrementalUpdate.py` script to update businesses that haven't been updated within the specified time threshold:

```bash
python incrementalUpdate.py
```


## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For questions or feedback, please contact [francesco.baldissera@gmail.com](mailto:yourname@example.com).
