#!/usr/bin/env python3
"""
Unit tests for Legacy Compatibility Layer
Tests LegacyScheduleAdapter and MigrationService
"""

import unittest
import tempfile
import os
from datetime import date, timedelta

from app import app, db, Student, ScheduleItem, ProjectPhase, PhaseTask, PhaseType
from app import LegacyScheduleAdapter, MigrationService

class TestLegacyCompatibility(unittest.TestCase):
    
    def setUp(self):
        """Set up test database"""
        self.db_fd, app.config['DATABASE'] = tempfile.mkstemp()
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        
        db.create_all()
        
        # Create legacy student
        self.legacy_student = Student(
            name="Legacy Student",
            email="legacy@example.com",
            project_title="Legacy Project",
            thesis_deadline=date.today() + timedelta(days=180),
            lit_review_deadline=date.today() + timedelta(days=90),
            work_days='{"monday": "light", "wednesday": "heavy"}',
            onboarded=True,
            is_multi_phase=False  # Legacy student
        )
        self.legacy_student.set_password("testpass")
        db.session.add(self.legacy_student)
        
        # Create multi-phase student
        self.multi_phase_student = Student(
            name="Multi-Phase Student",
            email="multiphase@example.com",
            project_title="Multi-Phase Project",
            thesis_deadline=date.today() + timedelta(days=180),
            lit_review_deadline=date.today() + timedelta(days=90),
            work_days='{"monday": "light", "wednesday": "heavy"}',
            onboarded=True,
            is_multi_phase=True  # Multi-phase student
        )
        self.multi_phase_student.set_password("testpass")
        db.session.add(self.multi_phase_student)
        
        db.session.commit()
        
        # Create legacy tasks
        self.legacy_tasks = []
        for i in range(3):
            task = ScheduleItem(
                student_id=self.legacy_student.id,
                date=date.today() + timedelta(days=i+1),
                task_description=f"Legacy task {i+1}",
                day_intensity="light",
                completed=(i == 0)  # First task completed
            )
            db.session.add(task)
            self.legacy_tasks.append(task)
        
        # Create multi-phase setup
        self.phase = ProjectPhase(
            student_id=self.multi_phase_student.id,
            phase_type=PhaseType.LITERATURE_REVIEW.value,
            phase_name="Literature Review",
            deadline=date.today() + timedelta(days=60),
            order_index=1
        )
        db.session.add(self.phase)
        db.session.commit()
        
        # Create phase tasks
        self.phase_tasks = []
        for i in range(3):
            task = PhaseTask(
                phase_id=self.phase.id,
                date=date.today() + timedelta(days=i+1),
                task_description=f"Phase task {i+1}",
                task_type="reading",
                day_intensity="light",
                completed=(i == 0)  # First task completed
            )
            db.session.add(task)
            self.phase_tasks.append(task)
        
        db.session.commit()
    
    def tearDown(self):
        """Clean up test database"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        os.close(self.db_fd)
    
    def test_legacy_adapter_get_student_tasks_legacy(self):
        """Test LegacyScheduleAdapter with legacy student"""
        tasks = LegacyScheduleAdapter.get_student_tasks(self.legacy_student.id)
        
        self.assertEqual(len(tasks), 3)
        self.assertIsInstance(tasks[0], ScheduleItem)
        
        # Test with date filter
        tomorrow = date.today() + timedelta(days=1)
        tasks_tomorrow = LegacyScheduleAdapter.get_student_tasks(
            self.legacy_student.id, date=tomorrow
        )
        self.assertEqual(len(tasks_tomorrow), 1)
        self.assertEqual(tasks_tomorrow[0].date, tomorrow)
        
        # Test with completed filter
        completed_tasks = LegacyScheduleAdapter.get_student_tasks(
            self.legacy_student.id, completed=True
        )
        self.assertEqual(len(completed_tasks), 1)
        self.assertTrue(completed_tasks[0].completed)
    
    def test_legacy_adapter_get_student_tasks_multiphase(self):
        """Test LegacyScheduleAdapter with multi-phase student"""
        tasks = LegacyScheduleAdapter.get_student_tasks(self.multi_phase_student.id)
        
        self.assertEqual(len(tasks), 3)
        self.assertIsInstance(tasks[0], PhaseTask)
        
        # Test with date filter
        tomorrow = date.today() + timedelta(days=1)
        tasks_tomorrow = LegacyScheduleAdapter.get_student_tasks(
            self.multi_phase_student.id, date=tomorrow
        )
        self.assertEqual(len(tasks_tomorrow), 1)
        self.assertEqual(tasks_tomorrow[0].date, tomorrow)
        
        # Test with completed filter
        completed_tasks = LegacyScheduleAdapter.get_student_tasks(
            self.multi_phase_student.id, completed=True
        )
        self.assertEqual(len(completed_tasks), 1)
        self.assertTrue(completed_tasks[0].completed)
    
    def test_legacy_adapter_get_upcoming_tasks(self):
        """Test getting upcoming tasks for both student types"""
        # Legacy student
        upcoming_legacy = LegacyScheduleAdapter.get_upcoming_tasks(self.legacy_student.id)
        self.assertEqual(len(upcoming_legacy), 2)  # 2 incomplete tasks
        self.assertIsInstance(upcoming_legacy[0], ScheduleItem)
        
        # Multi-phase student
        upcoming_multiphase = LegacyScheduleAdapter.get_upcoming_tasks(self.multi_phase_student.id)
        self.assertEqual(len(upcoming_multiphase), 2)  # 2 incomplete tasks
        self.assertIsInstance(upcoming_multiphase[0], PhaseTask)
    
    def test_legacy_adapter_get_tasks_by_date_range(self):
        """Test getting tasks by date range"""
        start_date = date.today()
        end_date = date.today() + timedelta(days=2)
        
        # Legacy student
        legacy_range_tasks = LegacyScheduleAdapter.get_tasks_by_date_range(
            self.legacy_student.id, start_date, end_date
        )
        self.assertEqual(len(legacy_range_tasks), 2)
        
        # Multi-phase student
        multiphase_range_tasks = LegacyScheduleAdapter.get_tasks_by_date_range(
            self.multi_phase_student.id, start_date, end_date
        )
        self.assertEqual(len(multiphase_range_tasks), 2)
    
    def test_legacy_adapter_get_task_counts(self):
        """Test getting task completion statistics"""
        # Legacy student
        legacy_counts = LegacyScheduleAdapter.get_task_counts(self.legacy_student.id)
        self.assertEqual(legacy_counts['total'], 3)
        self.assertEqual(legacy_counts['completed'], 1)
        self.assertEqual(legacy_counts['remaining'], 2)
        
        # Multi-phase student
        multiphase_counts = LegacyScheduleAdapter.get_task_counts(self.multi_phase_student.id)
        self.assertEqual(multiphase_counts['total'], 3)
        self.assertEqual(multiphase_counts['completed'], 1)
        self.assertEqual(multiphase_counts['remaining'], 2)
    
    def test_migration_service_can_migrate_student(self):
        """Test checking if student can be migrated"""
        # Legacy student should be migratable
        can_migrate, reason = MigrationService.can_migrate_student(self.legacy_student.id)
        self.assertTrue(can_migrate)
        self.assertEqual(reason, "Student can be migrated")
        
        # Multi-phase student should not be migratable
        cannot_migrate, reason = MigrationService.can_migrate_student(self.multi_phase_student.id)
        self.assertFalse(cannot_migrate)
        self.assertEqual(reason, "Student already using multi-phase system")
        
        # Non-existent student
        no_student, reason = MigrationService.can_migrate_student(99999)
        self.assertFalse(no_student)
        self.assertEqual(reason, "Student not found")
    
    def test_migration_service_get_migration_preview(self):
        """Test getting migration preview"""
        preview = MigrationService.get_migration_preview(self.legacy_student.id)
        
        self.assertIsNotNone(preview)
        self.assertEqual(preview['student']['name'], "Legacy Student")
        self.assertEqual(preview['migration_plan']['will_create_phase'], "Literature Review")
        self.assertEqual(preview['migration_plan']['tasks_to_migrate']['total_tasks'], 3)
        self.assertEqual(preview['migration_plan']['tasks_to_migrate']['completed_tasks'], 1)
        self.assertEqual(preview['migration_plan']['tasks_to_migrate']['pending_tasks'], 2)
    
    def test_migration_service_migrate_student(self):
        """Test migrating a legacy student"""
        # Verify student is legacy before migration
        self.assertFalse(self.legacy_student.is_multi_phase)
        
        # Perform migration
        result = MigrationService.migrate_student_to_multiphase(self.legacy_student.id)
        
        self.assertIsNotNone(result)
        self.assertTrue(result['success'])
        self.assertEqual(result['migrated_tasks'], 3)
        
        # Verify student is now multi-phase
        db.session.refresh(self.legacy_student)
        self.assertTrue(self.legacy_student.is_multi_phase)
        
        # Verify phase was created
        phases = ProjectPhase.query.filter_by(student_id=self.legacy_student.id).all()
        self.assertEqual(len(phases), 1)
        self.assertEqual(phases[0].phase_type, PhaseType.LITERATURE_REVIEW.value)
        
        # Verify tasks were migrated
        phase_tasks = PhaseTask.query.filter_by(phase_id=phases[0].id).all()
        self.assertEqual(len(phase_tasks), 3)
        
        # Verify task properties were preserved
        completed_phase_tasks = [t for t in phase_tasks if t.completed]
        self.assertEqual(len(completed_phase_tasks), 1)
    
    def test_migration_service_migrate_already_migrated(self):
        """Test migrating a student who is already multi-phase"""
        result = MigrationService.migrate_student_to_multiphase(self.multi_phase_student.id)
        self.assertIsNone(result)
    
    def test_migration_service_rollback(self):
        """Test rolling back a migration"""
        # First migrate the student
        MigrationService.migrate_student_to_multiphase(self.legacy_student.id)
        
        # Verify migration worked
        db.session.refresh(self.legacy_student)
        self.assertTrue(self.legacy_student.is_multi_phase)
        
        # Rollback migration
        success, message = MigrationService.rollback_migration(self.legacy_student.id)
        
        self.assertTrue(success)
        self.assertIn("Rolled back migration", message)
        
        # Verify rollback worked
        db.session.refresh(self.legacy_student)
        self.assertFalse(self.legacy_student.is_multi_phase)
        
        # Verify phases and tasks were deleted
        phases = ProjectPhase.query.filter_by(student_id=self.legacy_student.id).all()
        self.assertEqual(len(phases), 0)
    
    def test_migration_service_rollback_non_migrated(self):
        """Test rolling back a student who wasn't migrated"""
        success, message = MigrationService.rollback_migration(self.legacy_student.id)
        
        self.assertFalse(success)
        self.assertEqual(message, "Student not in multi-phase system")
    
    def test_legacy_adapter_nonexistent_student(self):
        """Test adapter behavior with non-existent student"""
        tasks = LegacyScheduleAdapter.get_student_tasks(99999)
        self.assertEqual(len(tasks), 0)
        
        upcoming = LegacyScheduleAdapter.get_upcoming_tasks(99999)
        self.assertEqual(len(upcoming), 0)
        
        counts = LegacyScheduleAdapter.get_task_counts(99999)
        self.assertEqual(counts['total'], 0)

if __name__ == '__main__':
    unittest.main()