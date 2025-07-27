import requests
import json
import os
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# load variables from .env
load_dotenv()

class Gsheet_agent:
    def __init__(self, ghseet_URL):
        self.scopes = ["https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive.file",
                "https://www.googleapis.com/auth/drive"]

        # load service account JSON
        json_content = json.loads(os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON_CONTENT"))
        self.creds = ServiceAccountCredentials.from_json_keyfile_dict(json_content, self.scopes)

        # Authorize the client
        self.client = gspread.authorize(self.creds)

        # open gsheet by link & select the first worksheet
        self.spreadsheet = self.client.open_by_url(ghseet_URL)
        self.sheet = self.spreadsheet.sheet1

        
    
    def write_to_sheet(self, row):
        success = self.sheet.append_row(row)
    
        if success:
            print("✅ Row added!")
        else:
            print(f"Something wrong happened: {success}")

    def json_string_to_dict(response):
        # remove the code fences and 'json' language hint
        clean_json_str = response.strip("`").lstrip("json").strip()
        # load as dict
        data = json.loads(clean_json_str)
        return data

    def query_gemini(query, text_only=True):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        headers = {
            "Content-Type": "application/json",
            "X-goog-api-key": os.getenv("GEMINI_API_KEY")
        }
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": f"{query}"
                        }
                    ]
                }
            ]
        }

        # Send POST request
        response = requests.post(url, headers=headers, json=payload)

        if not text_only:
            return response.json()
        else:
            return response.json()['candidates'][0]['content']['parts'][0]['text']




