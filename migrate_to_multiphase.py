#!/usr/bin/env python3
"""
Migration script to add multi-phase support to existing PaperPacer database
This script safely migrates existing users to the new multi-phase system
"""

from app import app, db, Student, ScheduleItem, ProjectPhase, PhaseTask, PhaseType
from datetime import datetime
import json

def migrate_existing_students():
    """Migrate existing students to multi-phase system"""
    print("Starting migration to multi-phase system...")
    
    with app.app_context():
        # Get all existing students who haven't been migrated yet
        students_to_migrate = Student.query.filter_by(is_multi_phase=False).all()
        
        print(f"Found {len(students_to_migrate)} students to migrate")
        
        for student in students_to_migrate:
            try:
                migrate_student_to_multiphase(student)
                print(f"✓ Migrated student: {student.name} ({student.email})")
            except Exception as e:
                print(f"✗ Failed to migrate student {student.name}: {str(e)}")
                # Continue with other students rather than failing completely
                continue
        
        db.session.commit()
        print("Migration completed successfully!")

def migrate_student_to_multiphase(student):
    """Migrate a single student to multi-phase system"""
    
    # Only migrate if student has been onboarded and has a lit review deadline
    if not student.onboarded or not student.lit_review_deadline:
        print(f"Skipping {student.name} - not fully onboarded")
        return
    
    # Create Literature Review phase using existing deadline
    lit_review_phase = ProjectPhase(
        student_id=student.id,
        phase_type=PhaseType.LITERATURE_REVIEW.value,
        phase_name="Literature Review",
        deadline=student.lit_review_deadline,
        is_active=True,
        order_index=1,
        created_at=datetime.utcnow()
    )
    
    db.session.add(lit_review_phase)
    db.session.flush()  # Get the phase ID
    
    # Migrate existing ScheduleItem tasks to PhaseTask
    existing_tasks = ScheduleItem.query.filter_by(student_id=student.id).all()
    
    for task in existing_tasks:
        phase_task = PhaseTask(
            phase_id=lit_review_phase.id,
            date=task.date,
            task_description=task.task_description,
            task_type='reading',  # Default to reading for literature review
            day_intensity=task.day_intensity,
            completed=task.completed,
            created_at=task.created_at
        )
        db.session.add(phase_task)
    
    # Mark student as migrated
    student.is_multi_phase = True
    
    print(f"  - Created Literature Review phase with {len(existing_tasks)} tasks")

def create_backup():
    """Create a backup of the current database before migration"""
    import shutil
    import os
    from datetime import datetime
    
    db_files = ['paperpacer.db', 'instance/paperpacer.db']
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    for db_file in db_files:
        if os.path.exists(db_file):
            backup_file = f"{db_file}.backup_{timestamp}"
            shutil.copy2(db_file, backup_file)
            print(f"Created backup: {backup_file}")

def verify_migration():
    """Verify that migration was successful"""
    with app.app_context():
        total_students = Student.query.count()
        migrated_students = Student.query.filter_by(is_multi_phase=True).count()
        
        print(f"\nMigration Verification:")
        print(f"Total students: {total_students}")
        print(f"Migrated students: {migrated_students}")
        print(f"Legacy students: {total_students - migrated_students}")
        
        # Check that phases were created
        total_phases = ProjectPhase.query.count()
        print(f"Total project phases created: {total_phases}")
        
        # Check that tasks were migrated
        total_phase_tasks = PhaseTask.query.count()
        total_schedule_items = ScheduleItem.query.count()
        print(f"Phase tasks created: {total_phase_tasks}")
        print(f"Original schedule items: {total_schedule_items}")

if __name__ == '__main__':
    print("PaperPacer Multi-Phase Migration Tool")
    print("=====================================")
    
    # Create backup first
    create_backup()
    
    # Run migration
    migrate_existing_students()
    
    # Verify results
    verify_migration()
    
    print("\nMigration complete! Existing users will now have Literature Review phase.")
    print("They can add additional phases through the settings page.")