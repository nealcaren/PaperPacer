#!/usr/bin/env python3
"""
Test script to create sample data and test migration
"""

from app import app, db, Student, ScheduleItem
from datetime import datetime, date, timedelta
import json

def create_test_data():
    """Create test data to test migration"""
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Create a test student with legacy data
        student = Student(
            name="Test Student",
            email="test@example.com",
            project_title="Test Thesis Project",
            thesis_deadline=date.today() + timedelta(days=180),
            lit_review_deadline=date.today() + timedelta(days=90),
            work_days='{"monday": "light", "wednesday": "heavy", "friday": "light"}',
            onboarded=True,
            is_multi_phase=False  # Legacy student
        )
        student.set_password("testpass")
        db.session.add(student)
        db.session.commit()
        
        # Create some schedule items for the student
        tasks = [
            "Read 3 academic articles on research topic",
            "Create bibliography of 20 sources",
            "Draft literature review outline",
            "Meet with advisor to discuss progress",
            "Revise research question based on readings"
        ]
        
        current_date = date.today() + timedelta(days=1)
        for i, task_desc in enumerate(tasks):
            task = ScheduleItem(
                student_id=student.id,
                date=current_date + timedelta(days=i*2),
                task_description=task_desc,
                day_intensity="light",
                completed=False
            )
            db.session.add(task)
        
        db.session.commit()
        print(f"Created test student: {student.name}")
        print(f"Created {len(tasks)} schedule items")
        
        return student.id

if __name__ == '__main__':
    student_id = create_test_data()
    print(f"Test data created successfully! Student ID: {student_id}")