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

        # open gsheet by link
        self.spreadsheet = self.client.open_by_url(ghseet_URL)

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



system_prompt = """
You are a parsing agent, your sole task is to identify the category, name, date, and amount of the expense from USER_MESSAGE.

Rules:
1. If you see a number followed by 'k', that most likely means 000, so 150k should be parsed as 150000.
2. Date format should be DD-MM-YYYY.
3. Only output the answer in dict format, nothing else

USER_MESSAGE:
"""

# ==============================================================
HELP_MESSAGE = """**📒 Expense Tracker Bot Help**

Hi! I'm your friendly expense tracker bot.
You can use me to log your expenses directly to Google Sheets.

**💡 How to use:**

```
$expense <your expense>
```

Or just mention me:

```
@ExpenseBot <your expense>
```

**✅ Example:**

```
$expense Lunch nasi goreng 25k today
```

Or

```
@ExpenseBot Coffee 50k 21-07-2025
```

I'll parse the message and add:

* **Category** (like Food, Transport, etc)
* **Name** (short name of the expense)
* **Date** (DD-MM-YYYY)
* **Amount** (numbers like 25k → 25000)

Your data goes straight into your Google Sheet.
Keep it neat and simple! 🧾✨

**Available Commands:**

* `$expense` → Log a new expense.
* `$expense-help` → Show this help message.

Happy tracking! 🗂️
"""

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'✅ Logged in as {client.user}')

@client.event
async def on_message(message):
    is_processing_expense = False
    if message.author == client.user:
        return

    if message.content.startswith("$expense-help"):
        await message.channel.send(HELP_MESSAGE)
        return

    if client.user in message.mentions:
        mention = f"<@{client.user.id}>"
        alt_mention = f"<@!{client.user.id}>"
        query = message.content.replace(mention, "").replace(alt_mention, "").strip()

        if not query:
            await message.channel.send("❌ Please provide expense details after mentioning me.")
            return

        is_processing_expense = True

    elif message.content == "$expense":
        await message.channel.send("❌ Please provide expense details.")
        return

    elif message.content.startswith("$expense "):
        query = message.content[len("$expense "):].strip()
        if not query:
            await message.channel.send("❌ Please provide expense details.")
            return
        is_processing_expense = True

    gsheet_URLs = {
        os.getenv("USER_1_ID") : os.getenv("USER_1_URL"),
        os.getenv("USER_2_ID") : os.getenv("USER_2_URL")
    }

    if is_processing_expense:
        author_gsheet_URL = gsheet_URLs.get(str(message.author.id))
        print(f"message.author.id:{message.author.id}")
        print(f"author_gsheet_URL:{author_gsheet_URL}")
        gsheet = Gsheet_agent(author_gsheet_URL)

        combined = system_prompt + query
        expense = json_string_to_dict(query_gemini(combined))

        print(f"expense:{expense}")

        row = [
            expense['category'],
            expense['name'],
            expense['date'],
            expense['amount'],
        ]

        gsheet.write_to_sheet(row)
        await message.channel.send(f"✅ Added to Google Sheet: {row}")
client.run(os.getenv("DISCORD_BOT_TOKEN"))
