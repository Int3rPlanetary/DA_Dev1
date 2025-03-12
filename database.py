"""Database configuration module."""
import os
import logging
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize SQLAlchemy
db = SQLAlchemy()

def init_db(app):
    """Initialize the database with the given Flask app."""
    try:
        # Initialize SQLAlchemy with the app
        db.init_app(app)
        
        # Test the database connection
        with app.app_context():
            engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
            connection = engine.connect()
            connection.close()
            logger.info("Database connection successful")
            
        return True
    except OperationalError as e:
        logger.error(f"Database connection error: {str(e)}")
        # If using PostgreSQL and it fails, try falling back to SQLite
        if 'postgresql' in app.config['SQLALCHEMY_DATABASE_URI']:
            logger.info("Falling back to SQLite database")
            app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///retronet_portal.db'
            db.init_app(app)
            return True
        return False
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        return False