#!/usr/bin/env python3

import unittest
import sys
import os
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import the app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, Student, ProjectPhase, PhaseTask, PhaseType, ScheduleItem
from werkzeug.security import generate_password_hash

class TestMultiPhaseRoutes(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        
        db.create_all()
        
        # Create multi-phase test user
        self.multi_phase_user = Student(
            name="Multi Phase User",
            email="multiphase@example.com",
            password_hash=generate_password_hash("password"),
            project_title="Multi Phase Project",
            thesis_deadline=datetime.now().date() + timedelta(days=180),
            lit_review_deadline=datetime.now().date() + timedelta(days=90),
            onboarded=True,
            is_multi_phase=True
        )
        
        # Create legacy test user
        self.legacy_user = Student(
            name="Legacy User",
            email="legacy@example.com",
            password_hash=generate_password_hash("password"),
            project_title="Legacy Project",
            thesis_deadline=datetime.now().date() + timedelta(days=180),
            lit_review_deadline=datetime.now().date() + timedelta(days=90),
            onboarded=True,
            is_multi_phase=False
        )
        
        db.session.add_all([self.multi_phase_user, self.legacy_user])
        db.session.commit()
        
        # Create test phases and tasks for multi-phase user
        self._create_test_data()
    
    def tearDown(self):
        """Clean up after tests"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def _create_test_data(self):
        """Create test phases and tasks"""
        today = datetime.now().date()
        
        # Create test phase
        self.test_phase = ProjectPhase(
            student_id=self.multi_phase_user.id,
            phase_type=PhaseType.LITERATURE_REVIEW.value,
            phase_name="Literature Review",
            deadline=today + timedelta(days=30),
            order_index=1,
            is_active=True
        )
        db.session.add(self.test_phase)
        db.session.commit()
        
        # Create test tasks
        self.test_task = PhaseTask(
            phase_id=self.test_phase.id,
            date=today,
            task_description="Test Task",
            task_type="reading",
            day_intensity="light",
            completed=False
        )
        
        # Create legacy task
        self.legacy_task = ScheduleItem(
            student_id=self.legacy_user.id,
            date=today,
            task_description="Legacy Task",
            day_intensity="light",
            completed=False
        )
        
        db.session.add_all([self.test_task, self.legacy_task])
        db.session.commit()
    
    def login_user(self, user):
        """Helper method to log in a user"""
        return self.app.post('/login', data={
            'email': user.email,
            'password': 'password'
        }, follow_redirects=True)
    
    def test_daily_checkin_multi_phase(self):
        """Test daily_checkin route with multi-phase user"""
        self.login_user(self.multi_phase_user)
        
        response = self.app.get('/daily_checkin')
        self.assertEqual(response.status_code, 200)
        
        # Should show multi-phase task
        self.assertIn(b'Test Task', response.data)
    
    def test_daily_checkin_legacy(self):
        """Test daily_checkin route with legacy user"""
        self.login_user(self.legacy_user)
        
        response = self.app.get('/daily_checkin')
        self.assertEqual(response.status_code, 200)
        
        # Should show legacy task
        self.assertIn(b'Legacy Task', response.data)
    
    def test_day_detail_multi_phase(self):
        """Test day_detail route with multi-phase user"""
        self.login_user(self.multi_phase_user)
        
        today_str = datetime.now().date().strftime('%Y-%m-%d')
        response = self.app.get(f'/day/{today_str}')
        self.assertEqual(response.status_code, 200)
        
        # Should show multi-phase task
        self.assertIn(b'Test Task', response.data)
    
    def test_day_detail_legacy(self):
        """Test day_detail route with legacy user"""
        self.login_user(self.legacy_user)
        
        today_str = datetime.now().date().strftime('%Y-%m-%d')
        response = self.app.get(f'/day/{today_str}')
        self.assertEqual(response.status_code, 200)
        
        # Should show legacy task
        self.assertIn(b'Legacy Task', response.data)
    
    def test_submit_progress_multi_phase(self):
        """Test submit_progress route with multi-phase user"""
        self.login_user(self.multi_phase_user)
        
        today_str = datetime.now().date().strftime('%Y-%m-%d')
        response = self.app.post('/submit_progress', data={
            'date': today_str,
            'completed_tasks': [str(self.test_task.id)],
            'notes': 'Test progress'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        # Verify task was marked as completed
        updated_task = PhaseTask.query.get(self.test_task.id)
        self.assertTrue(updated_task.completed)
    
    def test_submit_progress_legacy(self):
        """Test submit_progress route with legacy user"""
        self.login_user(self.legacy_user)
        
        today_str = datetime.now().date().strftime('%Y-%m-%d')
        response = self.app.post('/submit_progress', data={
            'date': today_str,
            'completed_tasks': [str(self.legacy_task.id)],
            'notes': 'Test progress'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        # Verify task was marked as completed
        updated_task = ScheduleItem.query.get(self.legacy_task.id)
        self.assertTrue(updated_task.completed)
    
    def test_update_day_intensity_multi_phase(self):
        """Test update_day_intensity route with multi-phase user"""
        self.login_user(self.multi_phase_user)
        
        today_str = datetime.now().date().strftime('%Y-%m-%d')
        response = self.app.post('/update_day_intensity', data={
            'date': today_str,
            'intensity': 'heavy'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        # Verify task intensity was updated
        updated_task = PhaseTask.query.get(self.test_task.id)
        self.assertEqual(updated_task.day_intensity, 'heavy')
    
    def test_update_day_intensity_legacy(self):
        """Test update_day_intensity route with legacy user"""
        self.login_user(self.legacy_user)
        
        today_str = datetime.now().date().strftime('%Y-%m-%d')
        response = self.app.post('/update_day_intensity', data={
            'date': today_str,
            'intensity': 'heavy'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        # Verify task intensity was updated
        updated_task = ScheduleItem.query.get(self.legacy_task.id)
        self.assertEqual(updated_task.day_intensity, 'heavy')
    
    def test_settings_multi_phase_display(self):
        """Test settings page displays phase management for multi-phase users"""
        self.login_user(self.multi_phase_user)
        
        response = self.app.get('/settings')
        self.assertEqual(response.status_code, 200)
        
        # Should show phase management section
        self.assertIn(b'Project Phases', response.data)
        self.assertIn(b'Literature Review', response.data)
    
    def test_settings_legacy_display(self):
        """Test settings page doesn't show phase management for legacy users"""
        self.login_user(self.legacy_user)
        
        response = self.app.get('/settings')
        self.assertEqual(response.status_code, 200)
        
        # Should not show phase management section
        self.assertNotIn(b'Project Phases', response.data)
        # Should show legacy lit review deadline field
        self.assertIn(b'Literature Review Deadline', response.data)
    
    def test_update_settings_phase_modification(self):
        """Test updating phase settings"""
        self.login_user(self.multi_phase_user)
        
        new_deadline = (datetime.now().date() + timedelta(days=45)).strftime('%Y-%m-%d')
        
        response = self.app.post('/update_settings', data={
            'project_title': 'Updated Project Title',
            'thesis_deadline': (datetime.now().date() + timedelta(days=200)).strftime('%Y-%m-%d'),
            'existing_phase_ids': [str(self.test_phase.id)],
            f'phase_name_{self.test_phase.id}': 'Updated Literature Review',
            f'phase_deadline_{self.test_phase.id}': new_deadline,
            'monday_intensity': 'light',
            'tuesday_intensity': 'heavy',
            'wednesday_intensity': 'light',
            'thursday_intensity': 'none',
            'friday_intensity': 'light',
            'saturday_intensity': 'none',
            'sunday_intensity': 'none'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        # Verify phase was updated
        updated_phase = ProjectPhase.query.get(self.test_phase.id)
        self.assertEqual(updated_phase.phase_name, 'Updated Literature Review')
        self.assertEqual(updated_phase.deadline.strftime('%Y-%m-%d'), new_deadline)
        
        # Verify user settings were updated
        updated_user = Student.query.get(self.multi_phase_user.id)
        self.assertEqual(updated_user.project_title, 'Updated Project Title')
    
    def test_update_settings_add_new_phase(self):
        """Test adding a new phase through settings"""
        self.login_user(self.multi_phase_user)
        
        response = self.app.post('/update_settings', data={
            'project_title': 'Test Project',
            'thesis_deadline': (datetime.now().date() + timedelta(days=200)).strftime('%Y-%m-%d'),
            'existing_phase_ids': [str(self.test_phase.id)],
            f'phase_name_{self.test_phase.id}': self.test_phase.phase_name,
            f'phase_deadline_{self.test_phase.id}': self.test_phase.deadline.strftime('%Y-%m-%d'),
            'new_phase_counter': ['1'],
            'new_phase_name_1': 'Research Question Development',
            'new_phase_type_1': 'research_question',
            'new_phase_deadline_1': (datetime.now().date() + timedelta(days=60)).strftime('%Y-%m-%d'),
            'monday_intensity': 'light',
            'tuesday_intensity': 'light',
            'wednesday_intensity': 'light',
            'thursday_intensity': 'none',
            'friday_intensity': 'light',
            'saturday_intensity': 'none',
            'sunday_intensity': 'none'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        # Verify new phase was created
        new_phases = ProjectPhase.query.filter_by(
            student_id=self.multi_phase_user.id,
            phase_name='Research Question Development'
        ).all()
        self.assertEqual(len(new_phases), 1)
        self.assertEqual(new_phases[0].phase_type, 'research_question')
    
    def test_update_settings_delete_phase(self):
        """Test deleting a phase through settings"""
        self.login_user(self.multi_phase_user)
        
        response = self.app.post('/update_settings', data={
            'project_title': 'Test Project',
            'thesis_deadline': (datetime.now().date() + timedelta(days=200)).strftime('%Y-%m-%d'),
            'delete_phase_ids': [str(self.test_phase.id)],
            'monday_intensity': 'light',
            'tuesday_intensity': 'light',
            'wednesday_intensity': 'light',
            'thursday_intensity': 'none',
            'friday_intensity': 'light',
            'saturday_intensity': 'none',
            'sunday_intensity': 'none'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        # Verify phase was deleted
        deleted_phase = ProjectPhase.query.get(self.test_phase.id)
        self.assertIsNone(deleted_phase)
        
        # Verify associated tasks were deleted
        deleted_task = PhaseTask.query.get(self.test_task.id)
        self.assertIsNone(deleted_task)
    
    def test_security_phase_access_control(self):
        """Test that users can't access other users' phases"""
        # Create another user with a phase
        other_user = Student(
            name="Other User",
            email="other@example.com",
            password_hash=generate_password_hash("password"),
            project_title="Other Project",
            thesis_deadline=datetime.now().date() + timedelta(days=180),
            lit_review_deadline=datetime.now().date() + timedelta(days=90),
            onboarded=True,
            is_multi_phase=True
        )
        db.session.add(other_user)
        db.session.commit()
        
        other_phase = ProjectPhase(
            student_id=other_user.id,
            phase_type=PhaseType.LITERATURE_REVIEW.value,
            phase_name="Other User's Phase",
            deadline=datetime.now().date() + timedelta(days=30),
            order_index=1,
            is_active=True
        )
        db.session.add(other_phase)
        db.session.commit()
        
        # Login as multi_phase_user and try to modify other user's phase
        self.login_user(self.multi_phase_user)
        
        response = self.app.post('/update_settings', data={
            'project_title': 'Test Project',
            'thesis_deadline': (datetime.now().date() + timedelta(days=200)).strftime('%Y-%m-%d'),
            'existing_phase_ids': [str(other_phase.id)],  # Try to modify other user's phase
            f'phase_name_{other_phase.id}': 'Hacked Phase Name',
            f'phase_deadline_{other_phase.id}': (datetime.now().date() + timedelta(days=45)).strftime('%Y-%m-%d'),
            'monday_intensity': 'light',
            'tuesday_intensity': 'light',
            'wednesday_intensity': 'light',
            'thursday_intensity': 'none',
            'friday_intensity': 'light',
            'saturday_intensity': 'none',
            'sunday_intensity': 'none'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        # Verify other user's phase was not modified
        unchanged_phase = ProjectPhase.query.get(other_phase.id)
        self.assertEqual(unchanged_phase.phase_name, "Other User's Phase")

if __name__ == '__main__':
    unittest.main()