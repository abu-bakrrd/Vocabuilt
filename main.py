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
        logger.info("Starting Telegram bot thread...")
        run_bot()
    except Exception as e:
        logger.error(f"Critical error in Telegram bot thread: {e}")

if __name__ == "__main__":
    # Start bot in a background thread
    bot_thread = threading.Thread(target=start_telegram_bot, name="BotThread")
    bot_thread.daemon = True
    bot_thread.start()
    logger.info("Telegram bot background thread started")
    
    # Start Flask server in the main thread
    try:
        logger.info("Starting Flask server on port 5000...")
        app.run(host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        logger.info("Shutting down precisely...")
    except Exception as e:
        logger.error(f"Flask server error: {e}")
