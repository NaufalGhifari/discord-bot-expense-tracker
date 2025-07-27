import os
import discord
from dotenv import load_dotenv
from parser_writer import Gsheet_agent

load_dotenv()

class Discord_bot:
    def __init__(self):
        self.intents = discord.Intents.default()
        self.intents.message_content = True
        self.client = discord.Client(intents=self.intents)
         
        # bind the handlers
        self.client.event(self.on_ready)
        self.client.event(self.on_message)
    
        self.HELP_MESSAGE = """**📒 Expense Tracker Bot Help**

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
        self.system_prompt = """
        You are a parsing agent, your sole task is to identify the category, name, date, and amount of the expense from USER_MESSAGE.

        Rules:
        1. If you see a number followed by 'k', that most likely means 000, so 150k should be parsed as 150000.
        2. Date format should be DD-MM-YYYY.
        3. Only output the answer in dict format, nothing else

        USER_MESSAGE:
        """

    def run(self):  
        self.client.run(os.getenv("DISCORD_BOT_TOKEN"))

    async def on_ready(self):
        print(f'✅ Logged in as {self.client.user}')

    async def on_message(self, message):
        is_processing_expense = False
        if message.author == self.client.user:
            return

        if message.content.startswith("$expense-help"):
            await message.channel.send(self.HELP_MESSAGE)
            return

        if self.client.user in message.mentions:
            mention = f"<@{self.client.user.id}>"
            alt_mention = f"<@!{self.client.user.id}>"
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

            row = gsheet.message_to_row(query)

            gsheet.write_to_sheet(row)
            await message.channel.send(f"✅ Added to Google Sheet: {row}")