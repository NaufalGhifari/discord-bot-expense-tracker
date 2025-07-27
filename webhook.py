from fastapi import FastAPI, Request
import threading
import uvicorn
from parser_writer import Gsheet_agent

class WebhookServer:
    def __init__(self):
        self.app = FastAPI()
        self.host = "0.0.0.0"
        self.port = 8000

        # Register routes
        self.app.post("/notify")(self.notify)


    async def notify(self, request: Request):
        data = await request.json()
        message = data.get("message")
        
        print(f"data: {data}")
        print(f"message:{message}")

        row = Gsheet_agent.message_to_row(message, auto=True)
        print(f"row:{row}")

        return {"status": "ok"}

    def run(self):
        uvicorn.run(self.app, host=self.host, port=self.port)

    def start(self):
        # Start in a separate thread so it won’t block
        thread = threading.Thread(target=self.run, daemon=True)
        thread.start()