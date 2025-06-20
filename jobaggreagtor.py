import requests
import os
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

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
    '"chief of staff"'
]

def build_query(domains, keywords):
    domain_query = " OR ".join(f"site:{d}" for d in domains)
    keyword_query = " OR ".join(keywords)
    return f"{domain_query} ({keyword_query})"

def search_jobs(query):
    params = {
        "engine": "google",
        "q": query,
        "api_key": SERPAPI_KEY,
        "tbs": "qdr:d",  # Past 24 hours
        "num": 100
    }

    response = requests.get(BASE_URL, params=params)
    if response.status_code != 200:
        raise Exception(f"Failed request: {response.status_code} — {response.text}")
    
    data = response.json()
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
    if not os.path.isfile(SERVICE_ACCOUNT_FILE):
        raise Exception(f"Service account JSON not found at: {SERVICE_ACCOUNT_FILE}")
    
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=SCOPES
    )
    gc = gspread.authorize(creds)
    return gc.open(SPREADSHEET_NAME).sheet1

def append_job_results_to_sheet(sheet, results):
    rows = []
    timestamp = datetime.utcnow().isoformat()
    for job in results:
        row = [timestamp, job['title'], job['link'], job['snippet']]
        rows.append(row)
    if rows:
        sheet.append_rows(rows, value_input_option='USER_ENTERED')

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
