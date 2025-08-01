#!/usr/bin/env python3
"""
Unit tests for Enhanced Onboarding Flow
Tests multi-phase project creation during onboarding
"""

import unittest
import tempfile
import os
from datetime import date, timedelta

from app import app, db, Student, ProjectPhase, PhaseTask

class TestEnhancedOnboarding(unittest.TestCase):
    
    def setUp(self):
        """Set up test database and client"""
        self.db_fd, app.config['DATABASE'] = tempfile.mkstemp()
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
        
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        
        db.create_all()
        
        # Create test user
        self.test_user = Student(
            name="Test User",
            email="test@example.com",
            onboarded=False,
            is_multi_phase=False
        )
        self.test_user.set_password("testpass")
        db.session.add(self.test_user)
        db.session.commit()
    
    def tearDown(self):
        """Clean up test database"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        os.close(self.db_fd)
    
    def login_test_user(self):
        """Helper to log in test user"""
        return self.app.post('/login', data={
            'email': 'test@example.com',
            'password': 'testpass'
        }, follow_redirects=True)
    
    def test_onboarding_page_loads(self):
        """Test that onboarding page loads correctly"""
        self.login_test_user()
        response = self.app.get('/onboard')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Let\'s Set Up Your Research Project', response.data)
        self.assertIn(b'Literature Review', response.data)
        self.assertIn(b'Research Question Development', response.data)
        self.assertIn(b'Methods Planning', response.data)
        self.assertIn(b'IRB Proposal', response.data)
    
    def test_single_phase_onboarding(self):
        """Test onboarding with single phase (Literature Review only)"""
        self.login_test_user()
        
        response = self.app.post('/submit_onboarding', data={
            'project_title': 'Test Research Project',
            'thesis_deadline': (date.today() + timedelta(days=180)).strftime('%Y-%m-%d'),
            'selected_phases': ['literature_review'],
            'literature_review_deadline': (date.today() + timedelta(days=60)).strftime('%Y-%m-%d'),
            'monday_intensity': 'light',
            'wednesday_intensity': 'heavy',
            'friday_intensity': 'light'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        # Verify user was onboarded
        db.session.refresh(self.test_user)
        self.assertTrue(self.test_user.onboarded)
        self.assertTrue(self.test_user.is_multi_phase)
        self.assertEqual(self.test_user.project_title, 'Test Research Project')
        
        # Verify phase was created
        phases = ProjectPhase.query.filter_by(student_id=self.test_user.id).all()
        self.assertEqual(len(phases), 1)
        self.assertEqual(phases[0].phase_type, 'literature_review')
        self.assertEqual(phases[0].phase_name, 'Literature Review')
        
        # Verify tasks were generated
        tasks = PhaseTask.query.filter_by(phase_id=phases[0].id).all()
        self.assertGreater(len(tasks), 0)
    
    def test_multi_phase_onboarding(self):
        """Test onboarding with multiple phases"""
        self.login_test_user()
        
        response = self.app.post('/submit_onboarding', data={
            'project_title': 'Multi-Phase Research Project',
            'thesis_deadline': (date.today() + timedelta(days=180)).strftime('%Y-%m-%d'),
            'selected_phases': ['literature_review', 'research_question', 'methods_planning'],
            'literature_review_deadline': (date.today() + timedelta(days=30)).strftime('%Y-%m-%d'),
            'research_question_deadline': (date.today() + timedelta(days=60)).strftime('%Y-%m-%d'),
            'methods_planning_deadline': (date.today() + timedelta(days=90)).strftime('%Y-%m-%d'),
            'monday_intensity': 'light',
            'tuesday_intensity': 'heavy',
            'thursday_intensity': 'light'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        # Verify user was onboarded
        db.session.refresh(self.test_user)
        self.assertTrue(self.test_user.onboarded)
        self.assertTrue(self.test_user.is_multi_phase)
        
        # Verify phases were created in correct order
        phases = ProjectPhase.query.filter_by(
            student_id=self.test_user.id
        ).order_by(ProjectPhase.order_index).all()
        
        self.assertEqual(len(phases), 3)
        self.assertEqual(phases[0].phase_type, 'literature_review')
        self.assertEqual(phases[0].order_index, 1)
        self.assertEqual(phases[1].phase_type, 'research_question')
        self.assertEqual(phases[1].order_index, 2)
        self.assertEqual(phases[2].phase_type, 'methods_planning')
        self.assertEqual(phases[2].order_index, 3)
        
        # Verify tasks were generated for each phase
        for phase in phases:
            tasks = PhaseTask.query.filter_by(phase_id=phase.id).all()
            self.assertGreater(len(tasks), 0)
    
    def test_onboarding_validation_no_phases(self):
        """Test validation when no phases are selected"""
        self.login_test_user()
        
        response = self.app.post('/submit_onboarding', data={
            'project_title': 'Test Project',
            'thesis_deadline': (date.today() + timedelta(days=180)).strftime('%Y-%m-%d'),
            'selected_phases': [],  # No phases selected
            'monday_intensity': 'light'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Please select at least one research phase', response.data)
        
        # Verify user was not onboarded
        db.session.refresh(self.test_user)
        self.assertFalse(self.test_user.onboarded)
    
    def test_onboarding_validation_invalid_deadlines(self):
        """Test validation with invalid deadline order"""
        self.login_test_user()
        
        response = self.app.post('/submit_onboarding', data={
            'project_title': 'Test Project',
            'thesis_deadline': (date.today() + timedelta(days=180)).strftime('%Y-%m-%d'),
            'selected_phases': ['literature_review', 'research_question'],
            'literature_review_deadline': (date.today() + timedelta(days=60)).strftime('%Y-%m-%d'),
            'research_question_deadline': (date.today() + timedelta(days=30)).strftime('%Y-%m-%d'),  # Before lit review
            'monday_intensity': 'light'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'chronological order', response.data)
        
        # Verify user was not onboarded
        db.session.refresh(self.test_user)
        self.assertFalse(self.test_user.onboarded)
    
    def test_onboarding_validation_past_deadline(self):
        """Test validation with past deadline"""
        self.login_test_user()
        
        response = self.app.post('/submit_onboarding', data={
            'project_title': 'Test Project',
            'thesis_deadline': (date.today() - timedelta(days=1)).strftime('%Y-%m-%d'),  # Past date
            'selected_phases': ['literature_review'],
            'literature_review_deadline': (date.today() + timedelta(days=30)).strftime('%Y-%m-%d'),
            'monday_intensity': 'light'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'must be in the future', response.data)
        
        # Verify user was not onboarded
        db.session.refresh(self.test_user)
        self.assertFalse(self.test_user.onboarded)
    
    def test_onboarding_validation_missing_deadline(self):
        """Test validation when phase deadline is missing"""
        self.login_test_user()
        
        response = self.app.post('/submit_onboarding', data={
            'project_title': 'Test Project',
            'thesis_deadline': (date.today() + timedelta(days=180)).strftime('%Y-%m-%d'),
            'selected_phases': ['literature_review', 'research_question'],
            'literature_review_deadline': (date.today() + timedelta(days=30)).strftime('%Y-%m-%d'),
            # Missing research_question_deadline
            'monday_intensity': 'light'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Please set a deadline', response.data)
        
        # Verify user was not onboarded
        db.session.refresh(self.test_user)
        self.assertFalse(self.test_user.onboarded)
    
    def test_onboarding_work_preferences_saved(self):
        """Test that work preferences are correctly saved"""
        self.login_test_user()
        
        self.app.post('/submit_onboarding', data={
            'project_title': 'Test Project',
            'thesis_deadline': (date.today() + timedelta(days=180)).strftime('%Y-%m-%d'),
            'selected_phases': ['literature_review'],
            'literature_review_deadline': (date.today() + timedelta(days=60)).strftime('%Y-%m-%d'),
            'monday_intensity': 'light',
            'tuesday_intensity': 'heavy',
            'wednesday_intensity': 'none',
            'thursday_intensity': 'light',
            'friday_intensity': 'none',
            'saturday_intensity': 'none',
            'sunday_intensity': 'none'
        }, follow_redirects=True)
        
        # Verify work preferences were saved correctly
        db.session.refresh(self.test_user)
        import json
        work_days = json.loads(self.test_user.work_days)
        
        expected_work_days = {
            'monday': 'light',
            'tuesday': 'heavy',
            'thursday': 'light'
        }
        
        self.assertEqual(work_days, expected_work_days)

if __name__ == '__main__':
    unittest.main()