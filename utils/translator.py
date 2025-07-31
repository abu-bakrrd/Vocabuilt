import json
import os
import random
import logging
from typing import Dict, Optional, List
from deep_translator import GoogleTranslator

from langdetect import detect  # добавь в начало файла
import re  # уже может быть подключен — проверь

def is_cyrillic(text: str) -> bool:
    """Определяет, состоит ли строка только из русских букв"""
    return bool(re.fullmatch(r"[А-Яа-яЁё]+", text.strip()))

logger = logging.getLogger(__name__)

class Translator:
    def __init__(self):
        self.dictionary = {}
        self.load_dictionary()
        # Initialize Google Translator for English to Russian
        try:
            self.google_translator = GoogleTranslator(source='en', target='ru')
            logger.info("Google Translator initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Google Translator: {e}")
            self.google_translator = None
    
    def load_dictionary(self):
        """Load dictionary from JSON file"""
        try:
            dict_path = os.path.join(os.path.dirname(__file__), 'dict.json')
            if os.path.exists(dict_path):
                with open(dict_path, 'r', encoding='utf-8') as f:
                    self.dictionary = json.load(f)
                logger.info(f"Loaded {len(self.dictionary)} words from dictionary")
            else:
                logger.warning("Dictionary file not found, using empty dictionary")
                self.dictionary = {}
        except Exception as e:
            logger.error(f"Error loading dictionary: {e}")
            self.dictionary = {}
    def translate(self, word: str) -> Optional[str]:
        """Translate word in either direction using language detection"""

        word_original = word.strip()
        word = word.lower().strip()

        if len(word) < 2 or not word.isalpha():
            return None

        # Определяем направление перевода вручную
        if is_cyrillic(word):
            source_lang = "ru"
            target_lang = "en"
        else:
            source_lang = "en"
            target_lang = "ru"

        try:
            translator = GoogleTranslator(source=source_lang, target=target_lang)
            translation = translator.translate(word_original)

            if translation and translation.lower() != word.lower():
                logger.info(f"Translation ({source_lang} → {target_lang}): '{word_original}' -> '{translation}'")
                return translation
        except Exception as e:
            logger.warning(f"Google Translate failed for '{word_original}': {e}")

        # fallback: если слово английское — ищем в словаре
        if source_lang == "en" and word in self.dictionary:
            translation = self.dictionary[word]
            if isinstance(translation, list):
                translation = ", ".join(translation)
            logger.info(f"Local dictionary: '{word_original}' -> '{translation}'")
            return translation

        return None

    def get_words_by_pattern(self, pattern: str) -> List[Dict[str, str]]:
        """Get words matching a pattern"""
        pattern = pattern.lower()
        matches = []
        
        for word, translation in self.dictionary.items():
            if pattern in word:
                if isinstance(translation, list):
                    translation = ", ".join(translation)
                matches.append({
                    'word': word,
                    'translation': translation
                })
        
        return matches
    
    def add_word(self, word: str, translation: str):
        """Add a word to the dictionary (runtime only)"""
        word = word.lower().strip()
        self.dictionary[word] = translation
    
    def get_dictionary_size(self) -> int:
        """Get the size of the dictionary"""
        return len(self.dictionary)
    
    def search_translation(self, translation_text: str) -> List[Dict[str, str]]:
        """Search for words by translation"""
        translation_text = translation_text.lower()
        matches = []
        
        for word, translation in self.dictionary.items():
            trans_str = translation
            if isinstance(translation, list):
                trans_str = ", ".join(translation).lower()
            else:
                trans_str = translation.lower()
            
            if translation_text in trans_str:
                matches.append({
                    'word': word,
                    'translation': translation if isinstance(translation, str) else ", ".join(translation)
                })
        
        return matches
