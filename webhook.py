from fastapi import FastAPI, Request
import threading
import uvicorn
from parser_writer import Gsheet_agent
import os

class WebhookServer:
    def __init__(self):
        self.app = FastAPI()
        self.host = "0.0.0.0"

        # Use Railway's assigned port if available
        self.port = int(os.getenv("PORT", 8000))

        # Register routes
        self.app.post("/notify")(self.notify)


    async def notify(self, request: Request):
        data = await request.json()
        message = data.get("message")
        gsheet_url = data.get("gsheet_url")
        gsheet = Gsheet_agent(gsheet_url)
        
        print(f"data: {data}")
        print(f"message:{message}")

        row = Gsheet_agent.message_to_row(message, auto=True)
        print(f"row:{row}")
        gsheet.write_to_sheet(row)

        return {"status": "ok",
                "message_received": f"{message}",
                "row":f"{row}"}

    def run(self):
        uvicorn.run(self.app, host=self.host, port=self.port)

    def start(self):
        # Start in a separate thread so it won’t block
        thread = threading.Thread(target=self.run, daemon=True)
        thread.start()