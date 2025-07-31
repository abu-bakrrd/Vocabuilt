from app import db
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    telegram_id = db.Column(db.String(50), unique=True, nullable=True)
    username = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with words
    words = relationship("Word", back_populates="user", cascade="all, delete-orphan")
    quiz_sessions = relationship("QuizSession", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<User {self.id}: {self.username}>'

class Word(db.Model):
    __tablename__ = 'words'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    english_word = db.Column(db.String(200), nullable=False)
    translation = db.Column(db.Text, nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with user
    user = relationship("User", back_populates="words")
    
    def __repr__(self):
        return f'<Word {self.english_word}: {self.translation}>'

class QuizSession(db.Model):
    __tablename__ = 'quiz_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    score = db.Column(db.Integer, default=0)
    total_questions = db.Column(db.Integer, default=0)
    quiz_type = db.Column(db.String(50), nullable=False)  # 'all', 'recent', 'random'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed = db.Column(db.Boolean, default=False)
    
    # Relationship with user
    user = relationship("User", back_populates="quiz_sessions")
    
    def __repr__(self):
        return f'<QuizSession {self.id}: {self.score}/{self.total_questions}>'
