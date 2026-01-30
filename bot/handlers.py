import sys
import os
import logging
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import db
from models import User, Word, QuizSession
from bot.buttons import BotButtons
from bot.quiz import QuizManager

logger = logging.getLogger(__name__)

class BotHandlers:
    def __init__(self, bot, translator):
        self.bot = bot
        self.translator = translator
        self.buttons = BotButtons()
        self.quiz_manager = QuizManager(bot)

    
    def get_or_create_user(self, telegram_user):
        """Get or create a user in the database"""
        from app import app
        with app.app_context():
            user = User.query.filter_by(telegram_id=str(telegram_user.id)).first()
            if not user:
                user = User(
                    telegram_id=str(telegram_user.id),
                    username=telegram_user.username or telegram_user.first_name
                )
                db.session.add(user)
                db.session.commit()
                db.session.refresh(user)
            return user
    
    def handle_start(self, message):
        """Handle /start command"""
        logger.info(f"User {message.from_user.id} (@{message.from_user.username}) started the bot")
        user = self.get_or_create_user(message.from_user)
        welcome_text = (
            f"🎯 Welcome to Vocabulary Bot, {user.username}!\n\n"
            "📚 Send me any English word and I'll translate it for you.\n"
            "➕ Use the 'Add to Dictionary' button to save words.\n\n"
            "Available commands:\n"
            "/test - Take a vocabulary quiz\n"
            "/delete - Manage your saved words\n"
            "/stop - Stop current quiz\n"
            "/help - Show this help message"
        )
        self.bot.send_message(message.chat.id, welcome_text)
    
    def handle_help(self, message):
        """Handle /help command"""
        help_text = (
            "🔤 **Vocabulary Bot Help**\n\n"
            "**Basic Usage:**\n"
            "• Send any English word → Get translation\n"
            "• Click 'Add to Dictionary' → Save to your personal dictionary\n\n"
            "**Commands:**\n"
            "/test - Start vocabulary quiz with options:\n"
            "  • All words - Test all your saved words\n"
            "  • Last 20 - Test your 20 most recent words\n"
            "  • Random 20 - Test 20 random words from your dictionary\n\n"
            "/delete - View and delete saved words\n"
            "/stop - Stop current quiz\n"
            "/help - Show this help message\n\n"
            "💡 **Tips:**\n"
            "• Build your vocabulary by adding words regularly\n"
            "• Take quizzes to test your knowledge\n"
            "• Use random quizzes for better retention"
        )
        self.bot.send_message(message.chat.id, help_text, parse_mode='Markdown')
    
    def handle_text_message(self, message):
        """Handle regular text messages (word translation requests)"""
        from app import app
        with app.app_context():
            if message.chat.id in self.quiz_manager.active_quizzes:
                # If user is in an active quiz, let quiz manager handle it
                return
            
            word = message.text.strip().lower()
            logger.info(f"User {message.from_user.id} requested translation for: '{word}'")
            
            # Get translation
            translation = self.translator.translate(word)
            
            if translation:
                # Send translation with "Add to Dictionary" button
                markup = self.buttons.add_to_dictionary_button(word, translation)
                response = f"🔤 **{word.title()}**\n📖 {translation}"
                self.bot.send_message(message.chat.id, response, 
                                    reply_markup=markup, parse_mode='Markdown')
            else:
                self.bot.send_message(message.chat.id, 
                                    "❌ Sorry, I couldn't find a translation for that word.")
    
    def handle_test(self, message):
        """Handle /test command"""
        from app import app
        with app.app_context():
            user = self.get_or_create_user(message.from_user)
            
            # Check if user has any words
            word_count = Word.query.filter_by(user_id=user.id).count()
            if word_count == 0:
                self.bot.send_message(message.chat.id, 
                                    "📚 You don't have any saved words yet! "
                                    "Send me some English words and add them to your dictionary first.")
                return
            
            # Show quiz options
            markup = self.buttons.quiz_options_keyboard()
            self.bot.send_message(message.chat.id, 
                                f"🎯 Choose your quiz type:\n\n"
                                f"📊 You have {word_count} saved words",
                                reply_markup=markup)
    
    def handle_delete(self, message):
        """Handle /delete command"""
        from app import app
        with app.app_context():
            user = self.get_or_create_user(message.from_user)
            
            # Get user's words
            words = Word.query.filter_by(user_id=user.id).order_by(Word.date_added.desc()).limit(20).all()
            
            if not words:
                self.bot.send_message(message.chat.id, 
                                    "📚 You don't have any saved words to delete.")
                return
            
            # Show words with delete buttons
            markup = self.buttons.delete_words_keyboard(words)
            word_list = "\n".join([f"• {word.english_word} - {word.translation}" for word in words[:10]])
            
            self.bot.send_message(message.chat.id, 
                                f"🗑️ **Your saved words** (showing up to 10):\n\n{word_list}\n\n"
                                "Click a button below to delete a word:",
                                reply_markup=markup, parse_mode='Markdown')
    
    def handle_stop(self, message):
        """Handle /stop command"""
        from app import app
        with app.app_context():
            if message.chat.id in self.quiz_manager.active_quizzes:
                quiz_data = self.quiz_manager.active_quizzes[message.chat.id]
                quiz_session = quiz_data['session']
                quiz_session.completed = True
                db.session.commit()
                del self.quiz_manager.active_quizzes[message.chat.id]
                
                self.bot.send_message(message.chat.id, 
                                    f"⏹️ Quiz stopped!\n"
                                    f"📊 Current Progress: {quiz_data['current_question']}/{quiz_session.total_questions}")
            else:
                self.bot.send_message(message.chat.id, "❌ No active quiz to stop.")
    
    def handle_callback_query(self, call):
        """Handle callback queries from inline keyboards"""
        from app import app
        with app.app_context():
            try:
                data = call.data
                user = self.get_or_create_user(call.from_user)
                
                if data.startswith('add_word:'):
                    word_to_add = data.split(':', 2)[1]
                    logger.info(f"User {call.from_user.id} adding word: '{word_to_add}'")
                    self._handle_add_word(call, user, data)
                elif data.startswith('quiz:'):
                    quiz_type = data.split(':')[1]
                    logger.info(f"User {call.from_user.id} starting quiz type: {quiz_type}")
                    self._handle_quiz_start(call, user, data)
                elif data.startswith('answer:'):
                    self._handle_quiz_answer(call, user, data)
                elif data.startswith('delete:'):
                    self._handle_delete_word(call, user, data)
                
                # Answer the callback to remove loading state
                self.bot.answer_callback_query(call.id)
                
            except Exception as e:
                logger.error(f"Error handling callback query: {e}")
                self.bot.answer_callback_query(call.id, "❌ An error occurred")
    
    def handle_poll_answer(self, poll_answer):
        """Handle poll answers for quiz questions"""
        try:
            self.quiz_manager.handle_poll_answer(poll_answer)
        except Exception as e:
            logger.error(f"Error handling poll answer: {e}")
    
    def _handle_add_word(self, call, user, data):
        """Handle adding word to dictionary"""
        try:
            # Parse data: add_word:english_word:translation
            parts = data.split(':', 2)
            if len(parts) != 3:
                return
            
            _, english_word, translation = parts
            
            # Check if word already exists
            existing_word = Word.query.filter_by(
                user_id=user.id, 
                english_word=english_word.lower()
            ).first()
            
            if existing_word:
                self.bot.edit_message_text(
                    f"📚 '{english_word}' is already in your dictionary!",
                    call.message.chat.id,
                    call.message.message_id
                )
            else:
                # Add new word
                new_word = Word(
                    user_id=user.id,
                    english_word=english_word.lower(),
                    translation=translation
                )
                db.session.add(new_word)
                db.session.commit()
                
                self.bot.edit_message_text(
                    f"✅ Added '{english_word}' to your dictionary!\n📖 {translation}",
                    call.message.chat.id,
                    call.message.message_id
                )
        except Exception as e:
            logger.error(f"Error adding word: {e}")
    
    def _handle_quiz_start(self, call, user, data):
        """Handle quiz start"""
        quiz_type = data.split(':')[1]  # quiz:all, quiz:recent, quiz:random
        
        # Start quiz session
        quiz_session_id = self.quiz_manager.start_quiz(call.message.chat.id, user.id, quiz_type)
        if quiz_session_id:
            # Note: sessions are managed within quiz_manager.active_quizzes
            self.bot.edit_message_text(
                "🎯 Starting quiz...",
                call.message.chat.id,
                call.message.message_id
            )
        else:
            self.bot.edit_message_text(
                "❌ Not enough words for this quiz type. You need at least 4 words.",
                call.message.chat.id,
                call.message.message_id
            )
    
    def _handle_quiz_answer(self, call, user, data):
        """Handle quiz answer"""
        if call.message.chat.id in self.active_quizzes:
            self.quiz_manager.handle_answer(call, self.active_quizzes[call.message.chat.id])
    
    def _handle_delete_word(self, call, user, data):
        """Handle word deletion"""
        try:
            word_id = int(data.split(':')[1])
            word = Word.query.filter_by(id=word_id, user_id=user.id).first()
            
            if word:
                word_text = f"{word.english_word} - {word.translation}"
                db.session.delete(word)
                db.session.commit()
                
                self.bot.edit_message_text(
                    f"🗑️ Deleted: {word_text}",
                    call.message.chat.id,
                    call.message.message_id
                )
            else:
                self.bot.edit_message_text(
                    "❌ Word not found or already deleted.",
                    call.message.chat.id,
                    call.message.message_id
                )
        except Exception as e:
            logger.error(f"Error deleting word: {e}")

    def handle_words(self, message):
    # """Handle /words command — show all user's saved words"""
        from app import app
        with app.app_context():
            user = self.get_or_create_user(message.from_user)

            # Получаем все слова пользователя
            words = Word.query.filter_by(user_id=user.id).order_by(Word.date_added.desc()).all()

            if not words:
                self.bot.send_message(message.chat.id, 
                                    "📚 Ваш словарь пуст. Добавьте слова, отправив их в чат.")
                return

            # Ограничим вывод до 50 слов (можно изменить)
            max_display = 50
            display_words = words[:max_display]
            word_list = "\n".join([f"• {w.english_word} — {w.translation}" for w in display_words])

            response = f"📖 **Ваш словарь** (всего: {len(words)} слов):\n\n{word_list}"
            if len(words) > max_display:
                response += f"\n\n...и ещё {len(words) - max_display} слов."

            self.bot.send_message(message.chat.id, response, parse_mode="Markdown")
