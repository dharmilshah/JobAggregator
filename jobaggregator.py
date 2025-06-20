import requests
import os
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

# Load .env locally if exists
load_dotenv()

# Get SerpAPI key from env variable
SERPAPI_KEY = os.getenv("SERPAPI_KEY")
if not SERPAPI_KEY:
    raise Exception("SERPAPI_KEY not found in environment variables")

# Get path to Google service account JSON file
# Locally, you can set SERVICE_ACCOUNT_FILE in .env or default path
# On Render, set SERVICE_ACCOUNT_FILE_PATH env var to point to the secret file location
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE_PATH", "service-account.json")

# Google Sheet name from env var or default
SPREADSHEET_NAME = os.getenv("SPREADSHEET_NAME", "Job Aggregator")

BASE_URL = "https://serpapi.com/search"

domains = [
    "boards.greenhouse.io",
    "jobs.lever.co",
    "hire.lever.co",
    "jobs.ashbyhq.com",
    "apply.workable.com",
    "ats.rippling.com",
    "app.welcometothejungle.com"
]

keywords = [
    '"business operations"',
    '"strategy associate"',
    '"chief of staff"',
    '"strategy & operations"',
    '"strategy and operations"',
    '"strategy analyst"',
    '"senior strategy analyst"',
]

def build_query(domains, keywords):
    domain_query = " OR ".join(f"site:{d}" for d in domains)
    keyword_query = " OR ".join(keywords)
    query = f"{domain_query} ({keyword_query})"
    logging.debug(f"Built search query: {query}")
    return query

def search_jobs(query):
    params = {
        "engine": "google",
        "q": query,
        "api_key": SERPAPI_KEY,
        "tbs": "qdr:d",  # Past 24 hours
        "num": 100
    }
    logging.debug(f"Sending request to SerpAPI with params: {params}")
    response = requests.get(BASE_URL, params=params)
    if response.status_code != 200:
        logging.error(f"Failed SerpAPI request: {response.status_code} — {response.text}")
        raise Exception(f"Failed request: {response.status_code} — {response.text}")
    
    data = response.json()
    logging.debug(f"Received {len(data.get('organic_results', []))} results from SerpAPI")
    return [
        {
            "title": r.get("title"),
            "link": r.get("link"),
            "snippet": r.get("snippet", "")
        }
        for r in data.get("organic_results", [])
    ]

# Google Sheets Setup
def get_gsheet():
    import pathlib
    logging.debug(f"Checking for service account file at {SERVICE_ACCOUNT_FILE}")
    if not os.path.isfile(SERVICE_ACCOUNT_FILE):
        logging.error(f"Service account JSON not found at: {SERVICE_ACCOUNT_FILE}")
        raise Exception(f"Service account JSON not found at: {SERVICE_ACCOUNT_FILE}")
    
    SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]
    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=SCOPES
    )
    logging.debug(f"Service account credentials created with scopes: {creds.scopes}")
    gc = gspread.authorize(creds)
    logging.debug("Authorized Google Sheets client successfully")
    sheet = gc.open(SPREADSHEET_NAME).sheet1
    logging.debug(f"Opened Google Sheet: {SPREADSHEET_NAME}")
    return sheet

def append_job_results_to_sheet(sheet, results):
    rows = []
    timestamp = datetime.utcnow().isoformat()
    for job in results:
        row = [timestamp, job['title'], job['link'], job['snippet']]
        rows.append(row)
    if rows:
        logging.debug(f"Appending {len(rows)} rows to Google Sheet")
        sheet.append_rows(rows, value_input_option='USER_ENTERED')
    else:
         logging.debug("No rows to append to Google Sheet")
def main():
    query = build_query(domains, keywords)
    results = search_jobs(query)
    return results

def run_job_aggregation():
    results = main()
    if results:
        sheet = get_gsheet()
        append_job_results_to_sheet(sheet, results)
    return results

if __name__ == "__main__":
    try:
        results = run_job_aggregation()
        if results:
            print(f"Appended {len(results)} job results to Google Sheet.")
        else:
            print("No job results found in the past 24 hours.")
    except Exception as e:
        print(f"Error during job search: {e}")
