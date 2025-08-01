#!/usr/bin/env python3

import unittest
import sys
import os
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import the app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, Student, ProjectPhase, PhaseTask, PhaseType
from werkzeug.security import generate_password_hash

class TestPhaseFiltering(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        
        db.create_all()
        
        # Create a test user with multi-phase project
        self.test_user = Student(
            name="Test User",
            email="test@example.com",
            password_hash=generate_password_hash("password"),
            project_title="Test Project",
            thesis_deadline=datetime.now().date() + timedelta(days=180),
            lit_review_deadline=datetime.now().date() + timedelta(days=90),
            onboarded=True,
            is_multi_phase=True
        )
        db.session.add(self.test_user)
        db.session.commit()
        
        # Create test phases
        self.phase1 = ProjectPhase(
            student_id=self.test_user.id,
            phase_type=PhaseType.LITERATURE_REVIEW.value,
            phase_name="Literature Review",
            deadline=datetime.now().date() + timedelta(days=60),
            order_index=1,
            is_active=True
        )
        
        self.phase2 = ProjectPhase(
            student_id=self.test_user.id,
            phase_type=PhaseType.RESEARCH_QUESTION.value,
            phase_name="Research Question Development",
            deadline=datetime.now().date() + timedelta(days=90),
            order_index=2,
            is_active=True
        )
        
        db.session.add(self.phase1)
        db.session.add(self.phase2)
        db.session.commit()
        
        # Create test tasks for each phase
        today = datetime.now().date()
        
        # Phase 1 tasks
        self.task1_p1 = PhaseTask(
            phase_id=self.phase1.id,
            date=today,
            task_description="Literature Review Task 1",
            task_type="reading",
            day_intensity="light",
            completed=False
        )
        
        self.task2_p1 = PhaseTask(
            phase_id=self.phase1.id,
            date=today + timedelta(days=1),
            task_description="Literature Review Task 2",
            task_type="reading",
            day_intensity="heavy",
            completed=True
        )
        
        # Phase 2 tasks
        self.task1_p2 = PhaseTask(
            phase_id=self.phase2.id,
            date=today + timedelta(days=2),
            task_description="Research Question Task 1",
            task_type="writing",
            day_intensity="light",
            completed=False
        )
        
        db.session.add_all([self.task1_p1, self.task2_p1, self.task1_p2])
        db.session.commit()
    
    def tearDown(self):
        """Clean up after tests"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def login_user(self):
        """Helper method to log in the test user"""
        return self.app.post('/login', data={
            'email': 'test@example.com',
            'password': 'password'
        }, follow_redirects=True)
    
    def test_remaining_tasks_no_filter(self):
        """Test remaining tasks page shows all tasks when no filter is applied"""
        self.login_user()
        
        response = self.app.get('/remaining_tasks')
        self.assertEqual(response.status_code, 200)
        
        # Should show tasks from both phases
        self.assertIn(b'Literature Review Task 1', response.data)
        self.assertIn(b'Research Question Task 1', response.data)
        
        # Should show phase filter dropdown
        self.assertIn(b'Filter by Phase', response.data)
        self.assertIn(b'Literature Review', response.data)
        self.assertIn(b'Research Question Development', response.data)
    
    def test_remaining_tasks_with_phase_filter(self):
        """Test remaining tasks page filters by specific phase"""
        self.login_user()
        
        # Filter by phase 1 (Literature Review)
        response = self.app.get(f'/remaining_tasks?phase={self.phase1.id}')
        self.assertEqual(response.status_code, 200)
        
        # Should show only phase 1 tasks
        self.assertIn(b'Literature Review Task 1', response.data)
        self.assertNotIn(b'Research Question Task 1', response.data)
        
        # Should show filtered phase name in title
        self.assertIn(b'Literature Review', response.data)
    
    def test_remaining_tasks_invalid_phase_filter(self):
        """Test remaining tasks page handles invalid phase filter gracefully"""
        self.login_user()
        
        # Use non-existent phase ID
        response = self.app.get('/remaining_tasks?phase=999')
        self.assertEqual(response.status_code, 200)
        
        # Should show all tasks when invalid filter is provided
        self.assertIn(b'Literature Review Task 1', response.data)
        self.assertIn(b'Research Question Task 1', response.data)
    
    def test_phase_detail_page(self):
        """Test phase detail page shows correct phase information"""
        self.login_user()
        
        response = self.app.get(f'/phase/{self.phase1.id}')
        self.assertEqual(response.status_code, 200)
        
        # Should show phase name and tasks
        self.assertIn(b'Literature Review', response.data)
        self.assertIn(b'Literature Review Task 1', response.data)
        self.assertIn(b'Literature Review Task 2', response.data)
        
        # Should not show tasks from other phases
        self.assertNotIn(b'Research Question Task 1', response.data)
    
    def test_phase_detail_unauthorized_access(self):
        """Test phase detail page prevents access to other users' phases"""
        # Create another user
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
        
        # Create phase for other user
        other_phase = ProjectPhase(
            student_id=other_user.id,
            phase_type=PhaseType.LITERATURE_REVIEW.value,
            phase_name="Other User's Phase",
            deadline=datetime.now().date() + timedelta(days=60),
            order_index=1,
            is_active=True
        )
        db.session.add(other_phase)
        db.session.commit()
        
        # Login as test user and try to access other user's phase
        self.login_user()
        response = self.app.get(f'/phase/{other_phase.id}')
        
        # Should redirect to dashboard with error message
        self.assertEqual(response.status_code, 302)
    
    def test_dashboard_phase_navigation(self):
        """Test dashboard shows phase navigation for multi-phase users"""
        self.login_user()
        
        response = self.app.get('/dashboard')
        self.assertEqual(response.status_code, 200)
        
        # Should show phase navigation
        self.assertIn(b'Research Phases', response.data)
        self.assertIn(b'Literature Review', response.data)
        self.assertIn(b'Research Question Development', response.data)
        
        # Should show phase progress
        self.assertIn(b'phase-progress', response.data)
    
    def test_legacy_user_no_phase_filtering(self):
        """Test that legacy users don't see phase filtering options"""
        # Create legacy user
        legacy_user = Student(
            name="Legacy User",
            email="legacy@example.com",
            password_hash=generate_password_hash("password"),
            project_title="Legacy Project",
            thesis_deadline=datetime.now().date() + timedelta(days=180),
            lit_review_deadline=datetime.now().date() + timedelta(days=90),
            onboarded=True,
            is_multi_phase=False
        )
        db.session.add(legacy_user)
        db.session.commit()
        
        # Login as legacy user
        self.app.post('/login', data={
            'email': 'legacy@example.com',
            'password': 'password'
        }, follow_redirects=True)
        
        response = self.app.get('/remaining_tasks')
        self.assertEqual(response.status_code, 200)
        
        # Should not show phase filtering
        self.assertNotIn(b'Filter by Phase', response.data)
        self.assertNotIn(b'Research Phases', response.data)

if __name__ == '__main__':
    unittest.main()