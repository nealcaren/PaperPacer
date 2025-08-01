#!/usr/bin/env python3
"""
Unit tests for Phase Navigation and Dashboard
Tests multi-phase dashboard and phase detail views
"""

import unittest
import tempfile
import os
from datetime import date, timedelta

from app import app, db, Student, ProjectPhase, PhaseTask, PhaseType, PhaseManager

class TestPhaseNavigation(unittest.TestCase):
    
    def setUp(self):
        """Set up test database and client"""
        self.db_fd, app.config['DATABASE'] = tempfile.mkstemp()
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        
        db.create_all()
        
        # Create multi-phase test user
        self.test_user = Student(
            name="Multi-Phase User",
            email="multiphase@example.com",
            project_title="Multi-Phase Research Project",
            thesis_deadline=date.today() + timedelta(days=180),
            lit_review_deadline=date.today() + timedelta(days=60),
            work_days='{"monday": "light", "wednesday": "heavy"}',
            onboarded=True,
            is_multi_phase=True
        )
        self.test_user.set_password("testpass")
        db.session.add(self.test_user)
        db.session.commit()
        
        # Create phases
        self.phases = []
        phase_configs = [
            ('literature_review', 'Literature Review', 30),
            ('research_question', 'Research Question Development', 60),
            ('methods_planning', 'Methods Planning', 90)
        ]
        
        for i, (phase_type, phase_name, days_offset) in enumerate(phase_configs, 1):
            phase = ProjectPhase(
                student_id=self.test_user.id,
                phase_type=phase_type,
                phase_name=phase_name,
                deadline=date.today() + timedelta(days=days_offset),
                order_index=i,
                is_active=True
            )
            db.session.add(phase)
            self.phases.append(phase)
        
        db.session.commit()
        
        # Create tasks for each phase
        for phase in self.phases:
            for i in range(3):
                task = PhaseTask(
                    phase_id=phase.id,
                    date=date.today() + timedelta(days=i+1),
                    task_description=f"Task {i+1} for {phase.phase_name}",
                    task_type="reading",
                    day_intensity="light",
                    completed=(i == 0)  # First task completed
                )
                db.session.add(task)
        
        db.session.commit()
        
        # Create legacy test user for comparison
        self.legacy_user = Student(
            name="Legacy User",
            email="legacy@example.com",
            project_title="Legacy Literature Review",
            thesis_deadline=date.today() + timedelta(days=180),
            lit_review_deadline=date.today() + timedelta(days=60),
            work_days='{"monday": "light", "wednesday": "heavy"}',
            onboarded=True,
            is_multi_phase=False
        )
        self.legacy_user.set_password("testpass")
        db.session.add(self.legacy_user)
        db.session.commit()
    
    def tearDown(self):
        """Clean up test database"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        os.close(self.db_fd)
    
    def login_user(self, email, password):
        """Helper to log in a user"""
        return self.app.post('/login', data={
            'email': email,
            'password': password
        }, follow_redirects=True)
    
    def test_multiphase_dashboard_loads(self):
        """Test that multi-phase dashboard loads correctly"""
        self.login_user('multiphase@example.com', 'testpass')
        response = self.app.get('/dashboard')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Research Phases', response.data)
        self.assertIn(b'Literature Review', response.data)
        self.assertIn(b'Research Question Development', response.data)
        self.assertIn(b'Methods Planning', response.data)
        self.assertIn(b'Overall Progress', response.data)
    
    def test_legacy_dashboard_loads(self):
        """Test that legacy dashboard still works"""
        self.login_user('legacy@example.com', 'testpass')
        response = self.app.get('/dashboard')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Literature Review Deadline', response.data)
        self.assertNotIn(b'Research Phases', response.data)
    
    def test_phase_detail_page_loads(self):
        """Test that phase detail page loads correctly"""
        self.login_user('multiphase@example.com', 'testpass')
        
        # Get first phase ID
        phase_id = self.phases[0].id
        response = self.app.get(f'/phase/{phase_id}')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Literature Review', response.data)
        self.assertIn(b'Phase Tasks', response.data)
        self.assertIn(b'Phase Tips', response.data)
        self.assertIn(b'Progress', response.data)
    
    def test_phase_detail_unauthorized_access(self):
        """Test that users can't access other users' phases"""
        self.login_user('legacy@example.com', 'testpass')
        
        # Try to access multi-phase user's phase
        phase_id = self.phases[0].id
        response = self.app.get(f'/phase/{phase_id}', follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Phase not found', response.data)
    
    def test_phase_detail_nonexistent_phase(self):
        """Test accessing non-existent phase"""
        self.login_user('multiphase@example.com', 'testpass')
        
        response = self.app.get('/phase/99999', follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Phase not found', response.data)
    
    def test_dashboard_helper_functions(self):
        """Test dashboard helper functions work correctly"""
        self.login_user('multiphase@example.com', 'testpass')
        
        with self.app.application.app_context():
            # Test phase progress calculation
            phase_progress = PhaseManager.get_phase_progress(self.phases[0].id)
            self.assertIsNotNone(phase_progress)
            self.assertEqual(phase_progress['total_tasks'], 3)
            self.assertEqual(phase_progress['completed_tasks'], 1)
            self.assertAlmostEqual(phase_progress['progress_percentage'], 33.3, places=1)
    
    def test_dashboard_shows_next_deadline(self):
        """Test that dashboard shows the next upcoming deadline"""
        self.login_user('multiphase@example.com', 'testpass')
        response = self.app.get('/dashboard')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Next Deadline', response.data)
        self.assertIn(b'Literature Review', response.data)  # Should be the next deadline
    
    def test_dashboard_shows_phase_progress(self):
        """Test that dashboard shows progress for each phase"""
        self.login_user('multiphase@example.com', 'testpass')
        response = self.app.get('/dashboard')
        
        self.assertEqual(response.status_code, 200)
        # Should show progress percentages
        self.assertIn(b'33%', response.data)  # Each phase has 1/3 tasks completed
    
    def test_phase_detail_shows_tasks(self):
        """Test that phase detail page shows tasks correctly"""
        self.login_user('multiphase@example.com', 'testpass')
        
        phase_id = self.phases[0].id
        response = self.app.get(f'/phase/{phase_id}')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Task 1 for Literature Review', response.data)
        self.assertIn(b'Task 2 for Literature Review', response.data)
        self.assertIn(b'Task 3 for Literature Review', response.data)
        
        # Should show completion status
        self.assertIn('✅'.encode('utf-8'), response.data)  # Completed task
        self.assertIn('⏳'.encode('utf-8'), response.data)  # Pending tasks
    
    def test_phase_detail_shows_tips(self):
        """Test that phase detail page shows relevant tips"""
        self.login_user('multiphase@example.com', 'testpass')
        
        # Test literature review phase tips
        lit_review_phase_id = self.phases[0].id
        response = self.app.get(f'/phase/{lit_review_phase_id}')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Start broad, then narrow', response.data)
        self.assertIn(b'Group sources by theme', response.data)
        
        # Test research question phase tips
        research_phase_id = self.phases[1].id
        response = self.app.get(f'/phase/{research_phase_id}')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'specific, measurable', response.data)
        self.assertIn(b'Can it be answered', response.data)

if __name__ == '__main__':
    unittest.main()