import requests
import json
import os
from dotenv import load_dotenv
import gspread
import discord
from oauth2client.service_account import ServiceAccountCredentials

# load variables from .env
load_dotenv()

class Gsheet_agent:
    def __init__(self):
        self.scopes = ["https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive.file",
                "https://www.googleapis.com/auth/drive"]

        # load service account JSON
        json_content = json.loads(os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON_CONTENT"))
        self.creds = ServiceAccountCredentials.from_json_keyfile_dict(json_content, self.scopes)

        # Authorize the client
        self.client = gspread.authorize(self.creds)

        # open gsheet by link
        self.spreadsheet = self.client.open_by_url("https://docs.google.com/spreadsheets/d/1fklDCTPnUQpNMpL1aVeIThXrJVwEcoaT7-VEvgEtPIQ/edit?gid=0#gid=0")

        # select the first worksheet
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

gsheet = Gsheet_agent()

system_prompt = """
You are a parsing agent, your sole task is to identify the category, name, date, and amount of the expense from USER_MESSAGE.

Rules:
1. If you see a number followed by 'k', that most likely means 000, so 150k should be parsed as 150000.
2. Date format should be DD-MM-YYYY.
3. Only output the answer in dict format, nothing else

USER_MESSAGE:
"""

# ==============================================================
intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'✅ Logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content.startswith("$expense"):
        query = message.content[len("$expense"):].strip()

        combined = system_prompt + query
        expense = json_string_to_dict(query_gemini(combined))

        print(f"expense:{expense}")

        row = []
        row.append(expense['category'])
        row.append(expense['name'])
        row.append(expense['date'])
        row.append(expense['amount'])

        gsheet.write_to_sheet(row)

        await message.channel.send(f"✅ Added to google sheet: {row}")
        
client.run(os.getenv("DISCORD_BOT_TOKEN"))