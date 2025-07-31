#!/usr/bin/env python3
"""Test Telegram bot connectivity"""
import os
import sys
import telebot
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_bot():
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        print("Error: TELEGRAM_BOT_TOKEN not found")
        return False
    
    try:
        bot = telebot.TeleBot(token)
        
        # Test the bot by getting its info
        bot_info = bot.get_me()
        print(f"Bot connected successfully!")
        print(f"Bot name: {bot_info.first_name}")
        print(f"Bot username: @{bot_info.username}")
        
        # Set up a simple handler
        @bot.message_handler(commands=['start'])
        def start_command(message):
            bot.reply_to(message, "Hello! Vocabulary bot is working!")
        
        @bot.message_handler(func=lambda message: True)
        def echo_all(message):
            bot.reply_to(message, f"You said: {message.text}")
        
        print("Starting bot polling...")
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
        
    except Exception as e:
        print(f"Bot error: {e}")
        return False

if __name__ == '__main__':
    test_bot()