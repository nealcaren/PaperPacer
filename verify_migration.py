#!/usr/bin/env python3
"""
Verify migration results
"""

from app import app, db, Student, ProjectPhase, PhaseTask, ScheduleItem

def verify_migration():
    """Verify that migration worked correctly"""
    with app.app_context():
        # Check student
        student = Student.query.first()
        print(f"Student: {student.name}")
        print(f"Is multi-phase: {student.is_multi_phase}")
        
        # Check phases
        phases = ProjectPhase.query.filter_by(student_id=student.id).all()
        print(f"\nProject Phases ({len(phases)}):")
        for phase in phases:
            print(f"  - {phase.phase_name} ({phase.phase_type})")
            print(f"    Deadline: {phase.deadline}")
            print(f"    Order: {phase.order_index}")
            print(f"    Active: {phase.is_active}")
        
        # Check phase tasks
        if phases:
            phase = phases[0]
            tasks = PhaseTask.query.filter_by(phase_id=phase.id).all()
            print(f"\nPhase Tasks for {phase.phase_name} ({len(tasks)}):")
            for task in tasks:
                print(f"  - {task.date}: {task.task_description}")
                print(f"    Type: {task.task_type}, Intensity: {task.day_intensity}")
                print(f"    Completed: {task.completed}")
                print(f"    Student ID (computed): {task.student_id}")
        
        # Check original schedule items still exist
        schedule_items = ScheduleItem.query.filter_by(student_id=student.id).all()
        print(f"\nOriginal Schedule Items ({len(schedule_items)}):")
        for item in schedule_items:
            print(f"  - {item.date}: {item.task_description}")

if __name__ == '__main__':
    verify_migration()