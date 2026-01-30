import sys
import os
import random
import logging
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import db
from models import User, Word, QuizSession
from bot.buttons import BotButtons

logger = logging.getLogger(__name__)

class QuizManager:
    def __init__(self, bot):
        self.bot = bot
        self.buttons = BotButtons()
        self.active_quizzes = {}  # Store current quiz sessions for each chat
        self.active_polls = {}   # Store poll_id -> quiz_session mapping
    
    def start_quiz(self, chat_id, user_id, quiz_type):
        """Start a new quiz session"""
        from app import app
        with app.app_context():
            try:
                # Get words based on quiz type
                words = self._get_quiz_words(user_id, quiz_type)
                
                if len(words) < 4:  # Need at least 4 words for multiple choice
                    return None
                
                # Create quiz session
                quiz_session = QuizSession(
                    user_id=user_id,
                    quiz_type=quiz_type,
                    total_questions=min(len(words), 20)  # Max 20 questions
                )
                db.session.add(quiz_session)
                db.session.commit()
                
                # Store quiz session
                self.active_quizzes[chat_id] = {
                    'session': quiz_session,
                    'words': words,
                    'current_question': 0,
                    'used_words': []  # Track used words to avoid repetition
                }
                
                # Start first question
                logger.info(f"Quiz started for user {user_id} (type: {quiz_type}, questions: {quiz_session.total_questions})")
                self._send_poll_question(chat_id, quiz_session, words)
                
                return quiz_session.id
                
            except Exception as e:
                logger.error(f"Error starting quiz: {e}")
                return None
    
    def _get_quiz_words(self, user_id, quiz_type):
        """Get words for quiz based on type"""
        if quiz_type == 'all':
            return Word.query.filter_by(user_id=user_id).all()
        elif quiz_type == 'recent':
            return Word.query.filter_by(user_id=user_id)\
                          .order_by(Word.date_added.desc())\
                          .limit(20).all()
        elif quiz_type == 'random':
            all_words = Word.query.filter_by(user_id=user_id).all()
            return random.sample(all_words, min(len(all_words), 20))
        else:
            return []
    
    def _send_poll_question(self, chat_id, quiz_session, available_words):
        """Send a quiz question using Telegram Poll"""
        from app import app
        with app.app_context():
            try:
                quiz_data = self.active_quizzes.get(chat_id)
                if not quiz_data:
                    return
                
                current_question = quiz_data['current_question'] + 1
                
                if current_question > quiz_session.total_questions:
                    self._finish_quiz(chat_id, quiz_session)
                    return
                
                # Select random word for question (avoid used words)
                used_word_ids = quiz_data.get('used_words', [])
                unused_words = [w for w in available_words if w.id not in used_word_ids]
                
                # If we've used all words, reset the used list
                if not unused_words:
                    unused_words = available_words
                    quiz_data['used_words'] = []
                    used_word_ids = []
                
                correct_word = random.choice(unused_words)
                quiz_data['used_words'].append(correct_word.id)
                
                # Get 3 other random words for wrong answers
                other_words = [w for w in available_words if w.id != correct_word.id]
                wrong_answers = random.sample(other_words, min(3, len(other_words)))
                
                # Create answer options
                all_options = [correct_word] + wrong_answers[:3]
                random.shuffle(all_options)
                
                # Find correct answer index and create option texts
                correct_index = None
                options = []
                for i, word in enumerate(all_options):
                    options.append(word.translation)
                    if word.id == correct_word.id:
                        correct_index = i
                
                # Create poll question
                question = f"🎯 Question {current_question}/{quiz_session.total_questions}\n🔤 What does '{correct_word.english_word}' mean?"
                
                # Send poll with automatic timer
                poll_message = self.bot.send_poll(
                    chat_id=chat_id,
                    question=question,
                    options=options,
                    type='quiz',
                    correct_option_id=correct_index,
                    is_anonymous=False,
                    explanation=f"✅ '{correct_word.english_word}' = '{correct_word.translation}'",
                    open_period=10  # Auto-close after 10 seconds
                )
                
                # Store poll data
                poll_id = poll_message.poll.id
                self.active_polls[poll_id] = {
                    'chat_id': chat_id,
                    'quiz_session': quiz_session,
                    'correct_word': correct_word,
                    'question_number': current_question,
                    'correct_index': correct_index  # Store the correct answer index
                }
                
                # Update current question number
                quiz_data['current_question'] = current_question
                
                # Schedule next question after poll timeout
                import threading
                def send_next_question():
                    import time
                    time.sleep(12)  # Wait for poll to close + 2 seconds
                    from app import app
                    with app.app_context():
                        if current_question < quiz_session.total_questions:
                            self._send_poll_question(chat_id, quiz_session, quiz_data['words'])
                        else:
                            self._finish_quiz(chat_id, quiz_session)
                            if chat_id in self.active_quizzes:
                                del self.active_quizzes[chat_id]
                
                threading.Thread(target=send_next_question, daemon=True).start()
                                
            except Exception as e:
                logger.error(f"Error sending poll question: {e}")
                self.bot.send_message(chat_id, "❌ Error generating question. Please try again.")
    
    def handle_poll_answer(self, poll_answer):
        """Handle poll answer"""
        from app import app
        with app.app_context():
            try:
                poll_id = poll_answer.poll_id
                user_id = poll_answer.user.id
                option_ids = poll_answer.option_ids
                
                if poll_id not in self.active_polls:
                    return
                
                poll_data = self.active_polls[poll_id]
                chat_id = poll_data['chat_id']
                quiz_session = poll_data['quiz_session']
                correct_word = poll_data['correct_word']
                question_number = poll_data['question_number']
                
                # Only process answers from the quiz participant
                if user_id != quiz_session.user_id:
                    return
                
                quiz_data = self.active_quizzes.get(chat_id)
                if not quiz_data:
                    return
                
                # Check if answer is correct and update score
                if option_ids and len(option_ids) > 0:
                    selected_option = option_ids[0]
                    correct_option = poll_data['correct_index']
                    
                    # Update score if answer is correct
                    if selected_option == correct_option:
                        quiz_session.score += 1
                        db.session.commit()
                        logger.info(f"Correct answer! Score updated to {quiz_session.score}")
                    else:
                        logger.info(f"Wrong answer. Score remains {quiz_session.score}")
                
                # Check if current question is completed
                # if question_number < quiz_session.total_questions:
                #     # Wait a bit for user to see the result, then send next question
                #     import time
                #     time.sleep(2)
                #     self._send_poll_question(chat_id, quiz_session, quiz_data['words'])
                # else:
                #     # Quiz finished
                #     self._finish_quiz(chat_id, quiz_session)
                #     # Clean up
                #     if chat_id in self.active_quizzes:
                #         del self.active_quizzes[chat_id]
                pass
                
                # Clean up this poll
                if poll_id in self.active_polls:
                    del self.active_polls[poll_id]
                    
            except Exception as e:
                logger.error(f"Error handling poll answer: {e}")
    

    
    def _finish_quiz(self, chat_id, quiz_session):
        """Finish the quiz and show results"""
        from app import app
        with app.app_context():
            try:
                quiz_session.completed = True
                db.session.commit()
                
                # Calculate percentage
                percentage = (quiz_session.score / quiz_session.total_questions) * 100
                logger.info(f"Quiz finished for user {quiz_session.user_id}: score {quiz_session.score}/{quiz_session.total_questions} ({percentage:.0f}%)")
                
                # Determine performance message
                if percentage >= 90:
                    performance = "🏆 Excellent!"
                elif percentage >= 70:
                    performance = "👏 Great job!"
                elif percentage >= 50:
                    performance = "👍 Good work!"
                else:
                    performance = "💪 Keep practicing!"
                
                results_text = (
                    f"🎯 **Quiz Complete!**\n\n"
                    f"{performance}\n"
                    f"📊 **Results:**\n"
                    f"✅ Correct: {quiz_session.score}\n"
                    f"❌ Wrong: {quiz_session.total_questions - quiz_session.score}\n"
                    f"📈 Score: {quiz_session.score}/{quiz_session.total_questions} ({percentage:.0f}%)\n\n"
                    f"💡 Keep adding new words and take more quizzes to improve!"
                )
                
                self.bot.send_message(chat_id, results_text, parse_mode='Markdown')
                
                # Clean up
                if chat_id in self.active_quizzes:
                    del self.active_quizzes[chat_id]
            except Exception as e:
                logger.error(f"Error finishing quiz: {e}")
