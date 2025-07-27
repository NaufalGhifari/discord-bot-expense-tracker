from fastapi import FastAPI, Request
import threading
import uvicorn

class WebhookServer:
    def __init__(self):
        self.app = FastAPI()
        self.host = "0.0.0.0"
        self.port = 8000

        # Register routes
        self.app.post("/notify")(self.notify)

    async def notify(self, request: Request):
        data = await request.json()
        print(f"data: {data}")
        
        # message = data.get("message")

        # Do your parsing here (Gemini or regex or other logic)
        # row = ["Test", message, "25-07-2025", 100000, "Auto"]
        # self.gsheet.write_to_sheet(row)

        return {"status": "ok"}

    def run(self):
        uvicorn.run(self.app, host=self.host, port=self.port)

    def start(self):
        # Start in a separate thread so it won’t block
        thread = threading.Thread(target=self.run, daemon=True)
        thread.start()