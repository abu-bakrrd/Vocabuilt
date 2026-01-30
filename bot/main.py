import os
import sys
import threading
import telebot
import logging
from datetime import datetime

# Add the parent directory to the path to import from other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import User, Word, QuizSession
from bot.handlers import BotHandlers
from utils.translator import Translator

# Logger is already configured in app.py
logger = logging.getLogger(__name__)

class VocabularyBot:
    def __init__(self):
        self.token = os.environ.get('TELEGRAM_BOT_TOKEN')
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")
        
        self.bot = telebot.TeleBot(self.token)
        self.translator = Translator()
        self.handlers = BotHandlers(self.bot, self.translator)
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup all bot command and message handlers"""
        
        @self.bot.message_handler(commands=['start'])
        def start_command(message):
            self.handlers.handle_start(message)
        
        @self.bot.message_handler(commands=['words'])
        def words_command(message):
            self.handlers.handle_words(message)

        @self.bot.message_handler(commands=['test'])
        def test_command(message):
            self.handlers.handle_test(message)
        
        @self.bot.message_handler(commands=['delete'])
        def delete_command(message):
            self.handlers.handle_delete(message)
        
        @self.bot.message_handler(commands=['stop'])
        def stop_command(message):
            self.handlers.handle_stop(message)
        
        @self.bot.message_handler(commands=['help'])
        def help_command(message):
            self.handlers.handle_help(message)
        
        @self.bot.message_handler(func=lambda message: True)
        def handle_text(message):
            self.handlers.handle_text_message(message)
        
        @self.bot.callback_query_handler(func=lambda call: True)
        def handle_callback(call):
            self.handlers.handle_callback_query(call)
        
        @self.bot.poll_answer_handler(func=lambda poll_answer: True)
        def handle_poll_answer(poll_answer): 
            self.handlers.handle_poll_answer(poll_answer)

        @self.bot.middleware_handler(update_types=['message'])
        def log_incoming_messages(bot_instance, message):
            logger.info(f"📩 Incoming message from {message.from_user.id} (@{message.from_user.username}): '{message.text}'")
    
    def run(self):
        """Start the bot"""
        logger.info("Starting Vocabulary Bot...")
        try:
            # Test bot connection first
            bot_info = self.bot.get_me()
            logger.info(f"Bot connected successfully as @{bot_info.username}")
            
            # Remove any existing webhooks to avoid 409 Conflict
            logger.info("Removing existing webhooks...")
            self.bot.remove_webhook()
            
            logger.info("Starting infinity polling...")
            self.bot.infinity_polling(timeout=20, long_polling_timeout=10)
        except Exception as e:
            logger.error(f"Bot error: {e}")
            raise

def run_bot():
    """Function to run the bot in a separate thread"""
    bot = VocabularyBot()
    bot.run()

if __name__ == '__main__':
    # Run bot in a separate thread if this script is called directly
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Keep the main thread alive
    try:
        bot_thread.join()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
