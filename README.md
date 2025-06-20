# JobAggregator
This Python project scrapes job listings from multiple job boards using SerpAPI, filters them by keywords, and appends the results to a Google Sheet. It also exposes a simple Flask API endpoint to trigger the job aggregation on demand.

Features
1. Queries Google via SerpAPI for jobs on specific domains and keywords
2. Appends results in batch to a Google Sheet with timestamp
3. Provides a /run-jobs HTTP endpoint to trigger the scraper remotely
4. Designed for easy deployment (e.g., on Render.com)

Prerequisites
1. Python 3.8+
2. Google Cloud Service Account JSON with Google Sheets API access
3. SerpAPI API key
4. A Google Sheet to store results, shared with the service account email

Environment Variables
Create a .env file locally or set environment variables in your hosting platform with the following:

Variable & description 
SERPAPI_KEY	                Your SerpAPI API key
SERVICE_ACCOUNT_FILE_PATH	  Path to your Google service account JSON file
SPREADSHEET_NAME	          Name of the Google Sheet where results will be appended
FLASK_ENV	(Optional)        set to development for debugging
