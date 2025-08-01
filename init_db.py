#!/usr/bin/env python3
"""
Database initialization script for PaperPacer
Run this to create/recreate the database with the correct schema
"""

from app import app, db
import os

def init_database():
    """Initialize the database with all tables"""
    with app.app_context():
        # Remove old database if it exists
        db_path = 'paperpacer.db'
        instance_db_path = 'instance/paperpacer.db'
        
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"Removed old database: {db_path}")
            
        if os.path.exists(instance_db_path):
            os.remove(instance_db_path)
            print(f"Removed old database: {instance_db_path}")
        
        # Create all tables
        db.create_all()
        print("Database tables created successfully!")
        print("Tables created:")
        print("- student (with authentication and password reset)")
        print("- schedule_item")
        print("- progress_log")
        print("- project_phase (new multi-phase support)")
        print("- phase_task (new multi-phase support)")

if __name__ == '__main__':
    init_database()