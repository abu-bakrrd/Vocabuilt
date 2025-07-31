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
