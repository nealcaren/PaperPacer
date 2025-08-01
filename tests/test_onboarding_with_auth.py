#!/usr/bin/env python3
"""
Test onboarding with proper authentication
"""

import requests
import subprocess
import time
import sys
import os
from datetime import datetime, timedelta

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def start_server():
    """Start the Flask development server"""
    print("Starting Flask server...")
    server_process = subprocess.Popen([
        sys.executable, "-c", 
        """
import sys
import os
sys.path.append('.')
from app import app
app.run(debug=False, port=5005, host='127.0.0.1')
        """
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait for server to start
    time.sleep(3)
    print("Flask server started on port 5005")
    return server_process

def create_test_user_and_login(base_url):
    """Create a test user and log in"""
    session = requests.Session()
    
    print("\n--- Creating test user and logging in ---")
    
    # Try to register a test user
    register_data = {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'testpassword123',
        'confirm_password': 'testpassword123'
    }
    
    try:
        # First, try to register
        response = session.post(f"{base_url}/register", data=register_data, timeout=10)
        if response.status_code == 200 and 'login' not in response.url:
            print("✅ Test user registered successfully")
        else:
            print("⚠️  Registration may have failed or user already exists")
    except Exception as e:
        print(f"⚠️  Registration request failed: {e}")
    
    # Try to log in
    login_data = {
        'username': 'testuser',
        'password': 'testpassword123'
    }
    
    try:
        response = session.post(f"{base_url}/login", data=login_data, timeout=10)
        if response.status_code == 200:
            # Check if we're redirected to dashboard or still on login page
            if 'login' in response.url or 'Login' in response.text:
                print("❌ Login failed - still on login page")
                return None
            else:
                print("✅ Login successful")
                return session
        else:
            print(f"❌ Login failed with status {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Login request failed: {e}")
        return None

def test_authenticated_onboarding(base_url):
    """Test onboarding with authentication"""
    
    # Create authenticated session
    session = create_test_user_and_login(base_url)
    if not session:
        print("❌ Could not create authenticated session")
        return False
    
    print("\n--- Testing authenticated onboarding ---")
    
    # Test 1: Access onboard route
    try:
        response = session.get(f"{base_url}/onboard", timeout=10)
        print(f"Onboard route status: {response.status_code}")
        
        if response.status_code == 200:
            html = response.text
            
            # Check for onboarding elements
            checks = [
                ('onboarding-form', 'Onboarding form'),
                ('next-btn', 'Next button'),
                ('project_title', 'Project title input'),
                ('thesis_deadline', 'Thesis deadline input'),
                ('OnboardingWizard', 'JavaScript class'),
                ('addEventListener', 'Event listeners'),
                ('selected_phases', 'Phase selection'),
                ('step-content', 'Step content divs')
            ]
            
            all_present = True
            for element, description in checks:
                if element in html:
                    print(f"✅ {description} found")
                else:
                    print(f"❌ {description} missing")
                    all_present = False
            
            if all_present:
                print("✅ All onboarding elements present")
                
                # Save the authenticated response for inspection
                with open('authenticated_onboard_response.html', 'w') as f:
                    f.write(html)
                print("✓ Full authenticated response saved to authenticated_onboard_response.html")
                
                return True
            else:
                print("❌ Some onboarding elements missing")
                return False
                
        else:
            print(f"❌ Onboard route returned {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to access authenticated onboard route: {e}")
        return False

def test_onboarding_submission(base_url):
    """Test onboarding form submission"""
    
    # Create authenticated session
    session = create_test_user_and_login(base_url)
    if not session:
        print("❌ Could not create authenticated session for submission test")
        return False
    
    print("\n--- Testing onboarding form submission ---")
    
    # Prepare form data
    form_data = {
        'project_title': 'Test Research Project',
        'thesis_deadline': (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d'),
        'selected_phases': ['literature_review'],
        'literature_review_deadline': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
        'monday_intensity': 'light',
        'tuesday_intensity': 'none',
        'wednesday_intensity': 'heavy',
        'thursday_intensity': 'none',
        'friday_intensity': 'light',
        'saturday_intensity': 'none',
        'sunday_intensity': 'none'
    }
    
    try:
        response = session.post(f"{base_url}/submit_onboarding", data=form_data, timeout=10)
        print(f"Submission status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Form submission successful")
            return True
        elif response.status_code == 302:
            print("✅ Form submission successful (redirected)")
            print(f"Redirect location: {response.headers.get('Location', 'Unknown')}")
            return True
        else:
            print(f"⚠️  Form submission returned {response.status_code}")
            print("Response content:", response.text[:500])
            return False
            
    except Exception as e:
        print(f"❌ Form submission failed: {e}")
        return False

def main():
    """Main test function"""
    server_process = None
    
    try:
        # Start the server
        server_process = start_server()
        base_url = "http://localhost:5005"
        
        print("="*60)
        print("AUTHENTICATED ONBOARDING TEST")
        print("="*60)
        
        # Test authenticated access
        onboard_success = test_authenticated_onboarding(base_url)
        
        # Test form submission
        submission_success = test_onboarding_submission(base_url)
        
        print("\n" + "="*60)
        print("TEST RESULTS")
        print("="*60)
        print(f"Authenticated Onboarding Access: {'✅ PASS' if onboard_success else '❌ FAIL'}")
        print(f"Form Submission: {'✅ PASS' if submission_success else '❌ FAIL'}")
        
        if onboard_success and submission_success:
            print("\n🎉 SUCCESS: Onboarding works correctly with authentication!")
            print("\nThe issue you experienced was likely:")
            print("1. Not being logged in when accessing /onboard")
            print("2. The route requires authentication (@login_required)")
            print("3. Users need to register/login first before onboarding")
        elif onboard_success:
            print("\n✅ Onboarding page loads correctly when authenticated")
            print("❌ But form submission has issues")
        else:
            print("\n❌ Onboarding has issues even when authenticated")
            print("Check the saved HTML file for debugging")
            
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Test failed with error: {e}")
    finally:
        # Stop the server
        if server_process:
            server_process.terminate()
            server_process.wait()
            print("Flask server stopped")

if __name__ == "__main__":
    main()