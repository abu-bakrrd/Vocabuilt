# Vocabulary Learning Application

## Overview

This is a comprehensive vocabulary learning application that combines both a Telegram bot and a web interface. Users can learn English words through interactive quizzes on Telegram and swipe-based vocabulary cards on the web. The application is built with Flask and uses PostgreSQL for data persistence.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

The application follows a modular Flask architecture with separate components for the web interface, Telegram bot, and shared utilities:

- **Backend**: Flask web framework with SQLAlchemy ORM
- **Database**: PostgreSQL with connection pooling and ping checks
- **Bot Framework**: pyTelegramBotAPI (telebot) for Telegram integration
- **Frontend**: Bootstrap-based responsive UI with touch gestures
- **Translation**: Google Translate API integration with local JSON dictionary fallback

## Key Components

### Database Models (`models.py`)
- **User**: Stores Telegram users with ID, username, and creation timestamp
- **Word**: User-specific vocabulary entries with English words and translations
- **QuizSession**: Tracks quiz attempts, scores, and completion status

### Telegram Bot (`bot/`)
- **BotHandlers**: Core message and command processing with poll answer handling
- **QuizManager**: Interactive quiz functionality using native Telegram polls
- **BotButtons**: Inline keyboard generation for user interactions

### Web Interface (`web/`, `templates/`, `static/`)
- **Routes**: Flask endpoints for word retrieval and saving
- **Frontend**: Swipe-based card interface using Hammer.js
- **Responsive Design**: Mobile-first Bootstrap implementation

### Utilities (`utils/`)
- **Translator**: Local dictionary lookup with JSON data source
- **Database Manager**: Connection handling and session management

## Data Flow

1. **Word Learning Flow**:
   - User encounters words via Telegram bot or web interface
   - Words are translated using local dictionary
   - Users can save words to their personal vocabulary
   - Saved words become available for quiz practice

2. **Quiz Flow**:
   - User initiates quiz via Telegram `/test` command
   - System generates multiple choice questions from user's vocabulary
   - Tracks scores and completion status in QuizSession model
   - Provides immediate feedback and final results

3. **Web Interaction Flow**:
   - Random words displayed in card format
   - Swipe right to save, swipe left to skip
   - Real-time statistics showing saved word count
   - AJAX-based word retrieval and saving

## External Dependencies

- **Flask**: Web framework and application structure
- **SQLAlchemy**: Database ORM and model management
- **pyTelegramBotAPI**: Telegram bot API integration
- **Bootstrap**: Frontend styling and responsive design
- **Hammer.js**: Touch gesture recognition for swipe functionality
- **PostgreSQL**: Primary data storage (configurable via DATABASE_URL)

## Deployment Strategy

The application is designed for cloud deployment with the following considerations:

- **Environment Variables**: 
  - `DATABASE_URL` for PostgreSQL connection
  - `TELEGRAM_BOT_TOKEN` for bot authentication
  - `SESSION_SECRET` for Flask sessions

- **Process Management**: 
  - Web server runs on Flask development server (port 5000)
  - Bot runs in separate thread to handle concurrent operations
  - Database connections use pooling for reliability

- **Scalability**: 
  - Stateless design allows horizontal scaling
  - Database connection pooling handles concurrent users
  - Session management through database storage

- **Error Handling**: 
  - Comprehensive logging throughout application
  - Graceful fallbacks for translation failures
  - Database transaction management with rollback capability

The application architecture prioritizes user experience with responsive design, real-time interactions, and multiple learning modalities while maintaining clean separation of concerns between web and bot functionality.