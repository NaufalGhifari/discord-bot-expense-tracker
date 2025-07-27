import requests
import json
import os
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timezone, timedelta

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

    def message_to_row(message, auto=False):
        system_prompt = """
        You are a parsing agent, your sole task is to identify the category, name, date, and amount of the expense from USER_MESSAGE.

        Rules:
        1. If you see a number followed by 'k', that most likely means 000, so 150k should be parsed as 150000.
        2. Date format should be DD-MM-YYYY.
        3. Only output the answer in dict format, nothing else

        USER_MESSAGE:
        """

        combined_query = system_prompt + message
        expense = Gsheet_agent.json_string_to_dict(Gsheet_agent.query_gemini(combined_query))
        print(f"expense:{expense}")

        # If not defined, set date to WIB today
        if expense['date'] == None:
            wib = timezone(timedelta(hours=7))
            now_wib = datetime.now(wib)
            formatted_date = now_wib.strftime("%d-%m-%Y")
            expense['date'] = formatted_date

        row = [
                expense['category'],
                expense['name'],
                expense['date'],
                expense['amount']
            ]
        if auto:
            row.append("Auto")
        return row


