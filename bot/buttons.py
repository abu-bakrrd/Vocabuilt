import telebot

class BotButtons:
    def add_to_dictionary_button(self, word, translation):
        """Create inline button to add word to dictionary"""
        markup = telebot.types.InlineKeyboardMarkup()
        callback_data = f"add_word:{word}:{translation}"
        button = telebot.types.InlineKeyboardButton(
            "➕ Add to Dictionary", 
            callback_data=callback_data
        )
        markup.add(button)
        return markup
    
    def quiz_options_keyboard(self):
        """Create keyboard for quiz options"""
        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        
        buttons = [
            telebot.types.InlineKeyboardButton("📚 All Words", callback_data="quiz:all"),
            telebot.types.InlineKeyboardButton("🕐 Last 20 Words", callback_data="quiz:recent"),
            telebot.types.InlineKeyboardButton("🎲 Random 20 Words", callback_data="quiz:random")
        ]
        
        markup.add(*buttons)
        return markup
    
    def quiz_question_keyboard(self, options, question_number):
        """Create keyboard for quiz question with multiple choice answers"""
        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        
        # Create answer buttons
        buttons = []
        for i, word in enumerate(options):
            letter = chr(65 + i)  # A, B, C, D
            button_text = f"{letter}) {word.translation}"
            callback_data = f"answer:{word.id}"
            button = telebot.types.InlineKeyboardButton(button_text, callback_data=callback_data)
            buttons.append(button)
        
        markup.add(*buttons)
        return markup
    
    def delete_words_keyboard(self, words):
        """Create keyboard for deleting words"""
        markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        
        buttons = []
        for word in words:
            button_text = f"🗑️ {word.english_word}"
            callback_data = f"delete:{word.id}"
            button = telebot.types.InlineKeyboardButton(button_text, callback_data=callback_data)
            buttons.append(button)
        
        # Add buttons in pairs
        for i in range(0, len(buttons), 2):
            if i + 1 < len(buttons):
                markup.add(buttons[i], buttons[i + 1])
            else:
                markup.add(buttons[i])
        
        return markup
