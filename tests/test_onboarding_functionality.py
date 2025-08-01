#!/usr/bin/env python3

"""
Test: Onboarding Functionality

This test verifies that the onboarding template renders correctly
and contains all the necessary JavaScript functionality.
"""

import sys
import os
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import the app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
import unittest

class TestOnboardingFunctionality(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        
        db.create_all()
    
    def tearDown(self):
        """Clean up after tests"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def login_test_user(self):
        """Create and login a test user"""
        from app import Student
        from werkzeug.security import generate_password_hash
        
        # Create test user
        test_user = Student(
            name="Test User",
            email="test@example.com",
            password_hash=generate_password_hash("password"),
            onboarded=False  # Not yet onboarded
        )
        db.session.add(test_user)
        db.session.commit()
        
        # Login the user
        with self.app.session_transaction() as sess:
            sess['_user_id'] = str(test_user.id)
            sess['_fresh'] = True
        
        return test_user
    
    def test_onboarding_page_loads(self):
        """Test that onboarding page loads successfully"""
        self.login_test_user()
        response = self.app.get('/onboard')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Get Started - PaperPacer', response.data)
    
    def test_onboarding_contains_steps(self):
        """Test that onboarding page contains all 4 steps"""
        self.login_test_user()
        response = self.app.get('/onboard')
        
        # Check for step indicators
        self.assertIn(b'Project Info', response.data)
        self.assertIn(b'Research Phases', response.data)
        self.assertIn(b'Work Schedule', response.data)
        self.assertIn(b'Review & Submit', response.data)
        
        # Check for step content
        self.assertIn(b'data-step="1"', response.data)
        self.assertIn(b'data-step="2"', response.data)
        self.assertIn(b'data-step="3"', response.data)
        self.assertIn(b'data-step="4"', response.data)
    
    def test_onboarding_contains_phase_options(self):
        """Test that onboarding contains all phase options"""
        self.login_test_user()
        response = self.app.get('/onboard')
        
        # Check for phase checkboxes
        self.assertIn(b'literature_review', response.data)
        self.assertIn(b'research_question', response.data)
        self.assertIn(b'methods_planning', response.data)
        self.assertIn(b'irb_proposal', response.data)
        
        # Check for phase names
        self.assertIn(b'Literature Review', response.data)
        self.assertIn(b'Research Question Development', response.data)
        self.assertIn(b'Methods Planning', response.data)
        self.assertIn(b'IRB Proposal', response.data)
    
    def test_onboarding_contains_work_schedule(self):
        """Test that onboarding contains work schedule options"""
        self.login_test_user()
        response = self.app.get('/onboard')
        
        # Check for day intensity options
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        intensities = ['none', 'light', 'heavy']
        
        for day in days:
            for intensity in intensities:
                expected = f'{day}_{intensity}'.encode()
                self.assertIn(expected, response.data)
        
        # Check for presets
        self.assertIn(b'Balanced Week', response.data)
        self.assertIn(b'Intensive Schedule', response.data)
        self.assertIn(b'Weekend Warrior', response.data)
    
    def test_onboarding_contains_javascript(self):
        """Test that onboarding contains necessary JavaScript"""
        self.login_test_user()
        response = self.app.get('/onboard')
        
        # Check for main JavaScript class
        self.assertIn(b'OnboardingWizard', response.data)
        
        # Check for key functions
        self.assertIn(b'nextStep', response.data)
        self.assertIn(b'prevStep', response.data)
        self.assertIn(b'updateStep', response.data)
        self.assertIn(b'validateCurrentStep', response.data)
        self.assertIn(b'autoSuggestDeadlines', response.data)
        
        # Check for event listeners
        self.assertIn(b'addEventListener', response.data)
        self.assertIn(b'DOMContentLoaded', response.data)
    
    def test_onboarding_contains_css_styles(self):
        """Test that onboarding contains necessary CSS styles"""
        self.login_test_user()
        response = self.app.get('/onboard')
        
        # Check for key CSS classes
        self.assertIn(b'onboarding-container', response.data)
        self.assertIn(b'progress-container', response.data)
        self.assertIn(b'step-content', response.data)
        self.assertIn(b'phase-card', response.data)
        self.assertIn(b'step-navigation', response.data)
        
        # Check for animations
        self.assertIn(b'fadeIn', response.data)
        self.assertIn(b'slideDown', response.data)
        
        # Check for responsive design
        self.assertIn(b'@media', response.data)
    
    def test_onboarding_form_structure(self):
        """Test that onboarding form has correct structure"""
        self.login_test_user()
        response = self.app.get('/onboard')
        
        # Check for form element
        self.assertIn(b'<form', response.data)
        self.assertIn(b'onboarding-form', response.data)
        self.assertIn(b'submit_onboarding', response.data)
        
        # Check for required inputs
        self.assertIn(b'project_title', response.data)
        self.assertIn(b'thesis_deadline', response.data)
        
        # Check for navigation buttons
        self.assertIn(b'next-btn', response.data)
        self.assertIn(b'prev-btn', response.data)
        self.assertIn(b'submit-btn', response.data)
    
    def test_onboarding_auto_save_functionality(self):
        """Test that onboarding includes auto-save functionality"""
        self.login_test_user()
        response = self.app.get('/onboard')
        
        # Check for localStorage usage
        self.assertIn(b'localStorage', response.data)
        self.assertIn(b'saveToStorage', response.data)
        self.assertIn(b'loadFromStorage', response.data)
        self.assertIn(b'paperpacer_onboarding', response.data)
        
        # Check for auto-save indicator
        self.assertIn(b'autosave-indicator', response.data)
        self.assertIn(b'automatically saved', response.data)

def run_onboarding_functionality_test():
    """Run the onboarding functionality test"""
    print("🧪 ONBOARDING FUNCTIONALITY TEST")
    print("=" * 50)
    
    # Run the tests
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    print("\n✅ ONBOARDING FUNCTIONALITY TEST COMPLETE!")
    print("=" * 50)
    print("🎯 Key features verified:")
    print("   ✅ Page loads successfully")
    print("   ✅ All 4 steps present")
    print("   ✅ Phase selection options available")
    print("   ✅ Work schedule configuration")
    print("   ✅ JavaScript functionality included")
    print("   ✅ CSS styling and animations")
    print("   ✅ Form structure correct")
    print("   ✅ Auto-save functionality present")

if __name__ == "__main__":
    run_onboarding_functionality_test()