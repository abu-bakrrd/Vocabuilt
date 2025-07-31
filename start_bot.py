#!/usr/bin/env python3
"""
Standalone Telegram bot runner
This script starts the Telegram bot independently
"""
import os
import sys
import logging
from bot.main import run_bot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

if __name__ == '__main__':
    if not os.getenv('TELEGRAM_BOT_TOKEN'):
        print("Error: TELEGRAM_BOT_TOKEN environment variable not set")
        sys.exit(1)
    
    print("Starting Telegram bot...")
    run_bot()