import os
import json
from datetime import datetime
from sqlalchemy import inspect
from flask import Flask
from database import db, init_db
from models import *  # Import all models

def backup_database():
    """Create a backup of the database schema and data"""
    print("Starting database backup...")
    
    # Create a minimal Flask app for database initialization
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+pg8000://postgres:postgres@localhost:5432/retronet_portal'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize the database connection
    init_db(app)
    
    # Create backup directory if it doesn't exist
    backup_dir = os.path.join(os.path.dirname(__file__), 'db_backup')
    os.makedirs(backup_dir, exist_ok=True)
    
    # Create a timestamp for the backup
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    backup_data = {}
    
    # Use Flask application context
    with app.app_context():
        # Get all models from the database
        inspector = inspect(db.engine)
        table_names = inspector.get_table_names()
        
        # For each table, get all data
        for table_name in table_names:
            print(f"Backing up table: {table_name}")
            try:
                # Execute raw SQL to get all data from the table
                result = db.session.execute(f"SELECT * FROM {table_name}")
                
                # Convert result to list of dictionaries
                rows = [dict(row) for row in result]
                
                # Store table data in backup_data
                backup_data[table_name] = rows
                
                # Get table schema
                columns = inspector.get_columns(table_name)
                backup_data[f"{table_name}_schema"] = [
                    {
                        "name": column["name"],
                        "type": str(column["type"]),
                        "nullable": column["nullable"],
                        "default": str(column["default"]) if column["default"] else None,
                    }
                    for column in columns
                ]
                
            except Exception as e:
                print(f"Error backing up table {table_name}: {str(e)}")
    
    # Save backup data to JSON file
    backup_file = os.path.join(backup_dir, f"db_backup_{timestamp}.json")
    with open(backup_file, 'w') as f:
        json.dump(backup_data, f, default=str, indent=2)
    
    print(f"Database backup completed and saved to {backup_file}")
    return backup_file

if __name__ == "__main__":
    backup_file = backup_database()
    print(f"Backup saved to: {backup_file}")