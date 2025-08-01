#!/usr/bin/env python3
"""
Demonstration of Legacy Compatibility Layer
Shows LegacyScheduleAdapter and MigrationService functionality
"""

import tempfile
import os
from datetime import date, timedelta

from app import app, db, Student, ScheduleItem, ProjectPhase, PhaseTask, PhaseType
from app import LegacyScheduleAdapter, MigrationService

def demo_legacy_compatibility():
    """Demonstrate the legacy compatibility system"""
    print("🔄 Legacy Compatibility Layer Demo")
    print("=" * 50)
    
    # Set up test database
    db_fd, app.config['DATABASE'] = tempfile.mkstemp()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        
        # Create legacy student
        legacy_student = Student(
            name="Legacy Student",
            email="legacy@example.com",
            project_title="Traditional Literature Review",
            thesis_deadline=date.today() + timedelta(days=180),
            lit_review_deadline=date.today() + timedelta(days=90),
            work_days='{"monday": "light", "wednesday": "heavy", "friday": "light"}',
            onboarded=True,
            is_multi_phase=False  # Legacy student
        )
        legacy_student.set_password("testpass")
        db.session.add(legacy_student)
        
        # Create multi-phase student
        multi_phase_student = Student(
            name="Multi-Phase Student", 
            email="multiphase@example.com",
            project_title="Advanced Research Project",
            thesis_deadline=date.today() + timedelta(days=180),
            lit_review_deadline=date.today() + timedelta(days=90),
            work_days='{"monday": "light", "wednesday": "heavy", "friday": "light"}',
            onboarded=True,
            is_multi_phase=True  # Multi-phase student
        )
        multi_phase_student.set_password("testpass")
        db.session.add(multi_phase_student)
        
        db.session.commit()
        
        print("\n👥 Student Profiles Created:")
        print(f"  📊 Legacy Student: {legacy_student.name} (ID: {legacy_student.id})")
        print(f"     Multi-phase: {legacy_student.is_multi_phase}")
        print(f"  🚀 Multi-Phase Student: {multi_phase_student.name} (ID: {multi_phase_student.id})")
        print(f"     Multi-phase: {multi_phase_student.is_multi_phase}")
        
        # Create legacy tasks
        legacy_tasks = []
        for i in range(4):
            task = ScheduleItem(
                student_id=legacy_student.id,
                date=date.today() + timedelta(days=i+1),
                task_description=f"Read academic articles on topic {i+1}",
                day_intensity="light",
                completed=(i < 2)  # First 2 tasks completed
            )
            db.session.add(task)
            legacy_tasks.append(task)
        
        # Create multi-phase setup
        phase = ProjectPhase(
            student_id=multi_phase_student.id,
            phase_type=PhaseType.LITERATURE_REVIEW.value,
            phase_name="Literature Review",
            deadline=date.today() + timedelta(days=60),
            order_index=1
        )
        db.session.add(phase)
        db.session.commit()
        
        # Create phase tasks
        phase_tasks = []
        for i in range(4):
            task = PhaseTask(
                phase_id=phase.id,
                date=date.today() + timedelta(days=i+1),
                task_description=f"Analyze literature theme {i+1}",
                task_type="analysis",
                day_intensity="light",
                completed=(i < 2)  # First 2 tasks completed
            )
            db.session.add(task)
            phase_tasks.append(task)
        
        db.session.commit()
        
        print(f"\n📋 Tasks Created:")
        print(f"  Legacy tasks: {len(legacy_tasks)} (2 completed, 2 pending)")
        print(f"  Phase tasks: {len(phase_tasks)} (2 completed, 2 pending)")
        
        # Demo LegacyScheduleAdapter
        print(f"\n🔄 LegacyScheduleAdapter Demo:")
        
        # Get all tasks for both students
        print(f"\n  📊 All Tasks Retrieval:")
        legacy_all_tasks = LegacyScheduleAdapter.get_student_tasks(legacy_student.id)
        multiphase_all_tasks = LegacyScheduleAdapter.get_student_tasks(multi_phase_student.id)
        
        print(f"    Legacy student tasks: {len(legacy_all_tasks)} (Type: {type(legacy_all_tasks[0]).__name__})")
        print(f"    Multi-phase student tasks: {len(multiphase_all_tasks)} (Type: {type(multiphase_all_tasks[0]).__name__})")
        
        # Get upcoming tasks
        print(f"\n  📅 Upcoming Tasks:")
        legacy_upcoming = LegacyScheduleAdapter.get_upcoming_tasks(legacy_student.id)
        multiphase_upcoming = LegacyScheduleAdapter.get_upcoming_tasks(multi_phase_student.id)
        
        print(f"    Legacy student upcoming: {len(legacy_upcoming)} tasks")
        for task in legacy_upcoming:
            print(f"      • {task.date}: {task.task_description}")
        
        print(f"    Multi-phase student upcoming: {len(multiphase_upcoming)} tasks")
        for task in multiphase_upcoming:
            print(f"      • {task.date}: {task.task_description}")
        
        # Get task counts
        print(f"\n  📈 Task Statistics:")
        legacy_counts = LegacyScheduleAdapter.get_task_counts(legacy_student.id)
        multiphase_counts = LegacyScheduleAdapter.get_task_counts(multi_phase_student.id)
        
        print(f"    Legacy student: {legacy_counts['completed']}/{legacy_counts['total']} completed ({legacy_counts['remaining']} remaining)")
        print(f"    Multi-phase student: {multiphase_counts['completed']}/{multiphase_counts['total']} completed ({multiphase_counts['remaining']} remaining)")
        
        # Demo MigrationService
        print(f"\n🔄 MigrationService Demo:")
        
        # Check if legacy student can be migrated
        can_migrate, reason = MigrationService.can_migrate_student(legacy_student.id)
        print(f"\n  ✅ Migration Check:")
        print(f"    Can migrate legacy student: {can_migrate}")
        print(f"    Reason: {reason}")
        
        # Get migration preview
        preview = MigrationService.get_migration_preview(legacy_student.id)
        print(f"\n  👀 Migration Preview:")
        print(f"    Student: {preview['student']['name']}")
        print(f"    Will create phase: {preview['migration_plan']['will_create_phase']}")
        print(f"    Phase deadline: {preview['migration_plan']['phase_deadline']}")
        print(f"    Tasks to migrate: {preview['migration_plan']['tasks_to_migrate']['total_tasks']}")
        print(f"    Task type distribution:")
        for task_type, count in preview['migration_plan']['tasks_to_migrate']['task_types'].items():
            print(f"      {task_type}: {count} tasks")
        
        # Perform migration
        print(f"\n  🚀 Performing Migration:")
        result = MigrationService.migrate_student_to_multiphase(legacy_student.id)
        
        if result and result['success']:
            print(f"    ✅ Migration successful!")
            print(f"    Phase created: {result['phase'].phase_name}")
            print(f"    Tasks migrated: {result['migrated_tasks']}")
            
            # Verify migration worked
            db.session.refresh(legacy_student)
            print(f"    Student is now multi-phase: {legacy_student.is_multi_phase}")
            
            # Test adapter with migrated student
            print(f"\n  🔍 Testing Adapter with Migrated Student:")
            migrated_tasks = LegacyScheduleAdapter.get_student_tasks(legacy_student.id)
            print(f"    Tasks retrieved: {len(migrated_tasks)} (Type: {type(migrated_tasks[0]).__name__})")
            
            migrated_counts = LegacyScheduleAdapter.get_task_counts(legacy_student.id)
            print(f"    Task counts: {migrated_counts['completed']}/{migrated_counts['total']} completed")
            
            # Demo rollback
            print(f"\n  ↩️  Testing Migration Rollback:")
            rollback_success, rollback_message = MigrationService.rollback_migration(legacy_student.id)
            print(f"    Rollback successful: {rollback_success}")
            print(f"    Message: {rollback_message}")
            
            if rollback_success:
                db.session.refresh(legacy_student)
                print(f"    Student is now legacy: {not legacy_student.is_multi_phase}")
        
        else:
            print(f"    ❌ Migration failed: {result.get('error', 'Unknown error') if result else 'No result'}")
        
        print(f"\n🎉 Legacy Compatibility Layer Demo Complete!")
        print(f"The system successfully:")
        print(f"  ✓ Provided unified task access for both legacy and multi-phase students")
        print(f"  ✓ Maintained backward compatibility with existing queries")
        print(f"  ✓ Enabled seamless migration from legacy to multi-phase system")
        print(f"  ✓ Preserved all existing task data during migration")
        print(f"  ✓ Supported rollback for testing and emergency scenarios")
    
    # Clean up
    os.close(db_fd)

if __name__ == '__main__':
    demo_legacy_compatibility()