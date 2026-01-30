import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "your-secret-key-here")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", 
    'sqlite:///vocabuilt.db'
)
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the app with the extension
db.init_app(app)

# Import routes after app creation to avoid circular imports
try:
    from web.routes import *
    logger.info("Web routes loaded successfully")
except ImportError:
    # If the web module is missing (e.g., bot-only mode), just log it
    logger.warning("Web module not found, running in bot-only mode")

with app.app_context():
    # Import models to ensure tables are created
    try:
        import models
        logger.info("Database models imported successfully")
        db.create_all()
        logger.info("Database tables verified/created successfully")
    except Exception as e:
        logger.error(f"Critical error during database initialization: {e}")
