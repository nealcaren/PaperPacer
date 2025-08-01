#!/usr/bin/env python3
"""
Test the fixed onboarding Next button functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
import unittest
from unittest.mock import patch

class TestOnboardingNextButton(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_onboarding_page_loads(self):
        """Test that the onboarding page loads without JavaScript errors"""
        response = self.app.get('/onboard')
        self.assertEqual(response.status_code, 200)
        
        # Check that the Next button is present
        self.assertIn(b'id="next-btn"', response.data)
        
        # Check that the JavaScript class is defined
        self.assertIn(b'class OnboardingWizard', response.data)
        
        # Check that the event listener is bound
        self.assertIn(b'addEventListener(\'click\', () => this.nextStep())', response.data)
        
        print("✓ Onboarding page loads successfully")
        print("✓ Next button is present")
        print("✓ JavaScript class is defined")
        print("✓ Event listener is bound")

    def test_no_duplicate_methods(self):
        """Test that there are no duplicate JavaScript methods"""
        response = self.app.get('/onboard')
        content = response.data.decode('utf-8')
        
        # Count occurrences of method definitions
        next_step_count = content.count('nextStep() {')
        prev_step_count = content.count('prevStep() {')
        update_step_count = content.count('updateStep() {')
        validate_current_step_count = content.count('validateCurrentStep() {')
        
        # Each method should appear only once
        self.assertEqual(next_step_count, 1, f"nextStep() appears {next_step_count} times, should be 1")
        self.assertEqual(prev_step_count, 1, f"prevStep() appears {prev_step_count} times, should be 1")
        self.assertEqual(update_step_count, 1, f"updateStep() appears {update_step_count} times, should be 1")
        self.assertEqual(validate_current_step_count, 1, f"validateCurrentStep() appears {validate_current_step_count} times, should be 1")
        
        print("✓ No duplicate nextStep() methods")
        print("✓ No duplicate prevStep() methods")
        print("✓ No duplicate updateStep() methods")
        print("✓ No duplicate validateCurrentStep() methods")

    def test_javascript_syntax_valid(self):
        """Test that the JavaScript doesn't have obvious syntax errors"""
        response = self.app.get('/onboard')
        content = response.data.decode('utf-8')
        
        # Check for balanced braces in the JavaScript section
        js_start = content.find('<script>')
        js_end = content.find('</script>')
        
        if js_start != -1 and js_end != -1:
            js_content = content[js_start:js_end]
            
            # Count braces
            open_braces = js_content.count('{')
            close_braces = js_content.count('}')
            
            self.assertEqual(open_braces, close_braces, 
                           f"Unbalanced braces: {open_braces} open, {close_braces} close")
            
            # Check for common syntax errors
            self.assertNotIn('function function', js_content, "Duplicate function keywords found")
            self.assertNotIn('class class', js_content, "Duplicate class keywords found")
            
            print("✓ JavaScript braces are balanced")
            print("✓ No obvious syntax errors found")

if __name__ == '__main__':
    print("Testing onboarding Next button fix...")
    print("=" * 50)
    
    unittest.main(verbosity=2)