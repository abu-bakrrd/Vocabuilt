import os
import threading
import logging
from app import app

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def start_telegram_bot():
    """Start the Telegram bot in a separate thread"""
    try:
        from bot.main import run_bot
        logger.info("Starting Telegram bot...")
        run_bot()
    except Exception as e:
        logger.error(f"Failed to start Telegram bot: {e}")


bot_thread = threading.Thread(target=start_telegram_bot, daemon=True)
bot_thread.start()
logger.info("Telegram bot thread started")

if __name__ == "__main__":
    # Start Flask server in the main thread
    # This keeps the app alive and provides a web interface if needed
    try:
        logger.info("Starting Flask server...")
        app.run(host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
