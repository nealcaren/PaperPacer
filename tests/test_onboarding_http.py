#!/usr/bin/env python3
"""
Test onboarding via HTTP requests to check if the issue is server-side
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
app.run(debug=False, port=5003, host='127.0.0.1')
        """
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait for server to start
    time.sleep(3)
    print("Flask server started on port 5003")
    return server_process

def test_onboarding_routes():
    """Test the onboarding routes"""
    base_url = "http://localhost:5003"
    
    print("="*60)
    print("ONBOARDING HTTP TEST")
    print("="*60)
    
    # Test 1: Check if onboard route is accessible
    print("\n--- Testing /onboard route ---")
    try:
        response = requests.get(f"{base_url}/onboard", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ /onboard route accessible")
            
            # Check if the HTML contains the expected elements
            html = response.text
            
            checks = [
                ('onboarding-form', 'Onboarding form'),
                ('next-btn', 'Next button'),
                ('project_title', 'Project title input'),
                ('thesis_deadline', 'Thesis deadline input'),
                ('OnboardingWizard', 'JavaScript class'),
                ('addEventListener', 'Event listeners')
            ]
            
            for element, description in checks:
                if element in html:
                    print(f"✅ {description} found")
                else:
                    print(f"❌ {description} missing")
                    
        elif response.status_code == 302:
            print("⚠️  /onboard route redirects (probably requires authentication)")
            print(f"Redirect location: {response.headers.get('Location', 'Unknown')}")
        else:
            print(f"❌ /onboard route returned {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to access /onboard route: {e}")
        return False
    
    # Test 2: Check if submit_onboarding route exists
    print("\n--- Testing /submit_onboarding route ---")
    try:
        # Try a POST request with minimal data
        data = {
            'project_title': 'Test Project',
            'thesis_deadline': (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d'),
            'selected_phases': 'literature_review',
            'literature_review_deadline': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
            'monday_intensity': 'light'
        }
        
        response = requests.post(f"{base_url}/submit_onboarding", data=data, timeout=10, allow_redirects=False)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 302:
            print("⚠️  /submit_onboarding redirects (probably requires authentication)")
        elif response.status_code == 200:
            print("✅ /submit_onboarding accepts POST requests")
        elif response.status_code == 405:
            print("❌ /submit_onboarding doesn't accept POST requests")
        else:
            print(f"⚠️  /submit_onboarding returned {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to access /submit_onboarding route: {e}")
    
    # Test 3: Check if static files are accessible
    print("\n--- Testing static files ---")
    try:
        response = requests.get(f"{base_url}/static/css/modern.css", timeout=10)
        if response.status_code == 200:
            print("✅ CSS file accessible")
        else:
            print(f"⚠️  CSS file returned {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to access CSS file: {e}")
    
    return True

def main():
    """Main test function"""
    server_process = None
    
    try:
        # Start the server
        server_process = start_server()
        
        # Run the tests
        success = test_onboarding_routes()
        
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        
        if success:
            print("✅ HTTP tests completed successfully")
            print("\nIf the /onboard route redirects, the issue might be:")
            print("1. Authentication required - user needs to be logged in")
            print("2. Session management - check if login is working")
            print("3. Route protection - @login_required decorator")
            print("\nIf the route is accessible but Next button doesn't work:")
            print("1. JavaScript errors in browser console")
            print("2. Validation logic blocking progression")
            print("3. Event binding issues")
        else:
            print("❌ HTTP tests failed")
            print("Check if the Flask server is running correctly")
            
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