from discord_bot import Discord_bot
from webhook import WebhookServer

def main():
    webhook = WebhookServer()
    webhook.start()

    bot = Discord_bot()
    bot.run()
    

if __name__ == "__main__":
    main()