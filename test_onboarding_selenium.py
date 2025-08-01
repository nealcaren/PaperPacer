#!/usr/bin/env python3
"""
Selenium test for onboarding Next button functionality
"""

import sys
import os
import time
import subprocess
import signal
from datetime import datetime, timedelta

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
except ImportError:
    print("Selenium not installed. Installing...")
    subprocess.run([sys.executable, "-m", "pip", "install", "selenium"])
    print("Selenium installed. Please run the test again.")
    sys.exit(1)

class OnboardingSeleniumTest:
    def __init__(self):
        self.server_process = None
        self.driver = None
        self.base_url = "http://localhost:5002"
        
    def start_server(self):
        """Start the Flask development server"""
        print("Starting Flask server...")
        self.server_process = subprocess.Popen([
            sys.executable, "-c", 
            """
import sys
import os
sys.path.append('.')
from app import app
app.run(debug=False, port=5002, host='127.0.0.1')
            """
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for server to start
        time.sleep(3)
        print("Flask server started on port 5002")
        
    def stop_server(self):
        """Stop the Flask server"""
        if self.server_process:
            self.server_process.terminate()
            self.server_process.wait()
            print("Flask server stopped")
    
    def setup_driver(self):
        """Setup Chrome WebDriver"""
        chrome_options = Options()
        # chrome_options.add_argument("--headless")  # Comment out to see browser
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1200,800")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
            print("✓ Chrome WebDriver initialized")
        except Exception as e:
            print(f"Failed to initialize Chrome WebDriver: {e}")
            print("Make sure ChromeDriver is installed and in PATH")
            raise
    
    def cleanup_driver(self):
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()
            print("WebDriver closed")
    
    def get_console_logs(self):
        """Get browser console logs"""
        try:
            logs = self.driver.get_log('browser')
            for log in logs:
                print(f"BROWSER CONSOLE: {log['level']} - {log['message']}")
        except Exception as e:
            print(f"Could not get console logs: {e}")
    
    def test_onboarding_flow(self):
        """Test the complete onboarding flow"""
        try:
            print(f"Navigating to {self.base_url}/onboard")
            self.driver.get(f"{self.base_url}/onboard")
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "onboarding-form"))
            )
            print("✓ Onboarding page loaded")
            
            # Check if we're on step 1
            step1 = self.driver.find_element(By.CSS_SELECTOR, '[data-step="1"].active')
            if step1:
                print("✓ Currently on Step 1")
            else:
                print("✗ Not on Step 1")
                return False
            
            # Test Step 1: Fill out project information
            print("\n--- Testing Step 1 ---")
            
            # Fill project title
            project_title = self.driver.find_element(By.ID, "project_title")
            project_title.clear()
            project_title.send_keys("Test Research Project")
            print("✓ Filled project title")
            
            # Fill thesis deadline (90 days from now)
            future_date = (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d")
            thesis_deadline = self.driver.find_element(By.ID, "thesis_deadline")
            thesis_deadline.clear()
            thesis_deadline.send_keys(future_date)
            print(f"✓ Filled thesis deadline: {future_date}")
            
            # Get console logs before clicking
            print("Console logs before clicking Next:")
            self.get_console_logs()
            
            # Click Next button
            print("Clicking Next button...")
            next_button = self.driver.find_element(By.ID, "next-btn")
            next_button.click()
            print("✓ Next button clicked")
            
            # Wait a moment for transition
            time.sleep(2)
            
            # Get console logs after clicking
            print("Console logs after clicking Next:")
            self.get_console_logs()
            
            # Check if we advanced to step 2
            try:
                step2 = self.driver.find_element(By.CSS_SELECTOR, '[data-step="2"].active')
                print("✅ SUCCESS: Advanced to Step 2!")
            except NoSuchElementException:
                print("❌ FAILED: Still on Step 1")
                # Check what step we're actually on
                for i in range(1, 5):
                    try:
                        step = self.driver.find_element(By.CSS_SELECTOR, f'[data-step="{i}"].active')
                        print(f"Currently on step: {i}")
                        break
                    except NoSuchElementException:
                        continue
                return False
            
            # Test Step 2: Research Phases
            print("\n--- Testing Step 2 ---")
            
            # Check if literature review is already selected
            lit_review = self.driver.find_element(By.ID, "phase_literature_review")
            if not lit_review.is_selected():
                lit_review.click()
                print("✓ Checked literature review")
            else:
                print("✓ Literature review already checked")
            
            # Fill the deadline for literature review
            deadline_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
            lit_deadline = self.driver.find_element(By.ID, "literature_review_deadline")
            lit_deadline.clear()
            lit_deadline.send_keys(deadline_date)
            print(f"✓ Filled literature review deadline: {deadline_date}")
            
            # Click Next button for step 2
            print("Clicking Next button for Step 2...")
            next_button.click()
            time.sleep(2)
            
            # Get console logs
            print("Console logs after Step 2 Next:")
            self.get_console_logs()
            
            # Check if we advanced to step 3
            try:
                step3 = self.driver.find_element(By.CSS_SELECTOR, '[data-step="3"].active')
                print("✅ SUCCESS: Advanced to Step 3!")
            except NoSuchElementException:
                print("❌ FAILED: Could not advance from Step 2")
                # Check current step
                for i in range(1, 5):
                    try:
                        step = self.driver.find_element(By.CSS_SELECTOR, f'[data-step="{i}"].active')
                        print(f"Currently on step: {i}")
                        break
                    except NoSuchElementException:
                        continue
                return False
            
            # Test Step 3: Work Schedule
            print("\n--- Testing Step 3 ---")
            
            # Select some work days
            monday_light = self.driver.find_element(By.CSS_SELECTOR, 'input[name="monday_intensity"][value="light"]')
            monday_light.click()
            tuesday_heavy = self.driver.find_element(By.CSS_SELECTOR, 'input[name="tuesday_intensity"][value="heavy"]')
            tuesday_heavy.click()
            print("✓ Selected work schedule")
            
            # Click Next button for step 3
            print("Clicking Next button for Step 3...")
            next_button.click()
            time.sleep(2)
            
            # Check if we advanced to step 4
            try:
                step4 = self.driver.find_element(By.CSS_SELECTOR, '[data-step="4"].active')
                print("✅ SUCCESS: Advanced to Step 4!")
                
                # Check if submit button is visible
                try:
                    submit_button = self.driver.find_element(By.ID, "submit-btn")
                    is_visible = submit_button.is_displayed()
                    print(f"✓ Submit button visible: {is_visible}")
                except NoSuchElementException:
                    print("✗ Submit button not found")
                    
            except NoSuchElementException:
                print("❌ FAILED: Could not advance from Step 3")
                return False
            
            print("\n🎉 ALL TESTS PASSED! Onboarding flow works correctly!")
            return True
            
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            self.get_console_logs()
            return False
    
    def test_validation_blocking(self):
        """Test that validation properly blocks progression"""
        try:
            print(f"\n--- Testing Validation Blocking ---")
            self.driver.get(f"{self.base_url}/onboard")
            
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "onboarding-form"))
            )
            
            # Try to click Next without filling anything
            print("Trying to advance without filling required fields...")
            next_button = self.driver.find_element(By.ID, "next-btn")
            next_button.click()
            time.sleep(1)
            
            # Get console logs
            print("Console logs after empty form Next click:")
            self.get_console_logs()
            
            # Should still be on step 1
            try:
                step1 = self.driver.find_element(By.CSS_SELECTOR, '[data-step="1"].active')
                print("✅ GOOD: Validation blocked progression (still on Step 1)")
            except NoSuchElementException:
                print("❌ BAD: Validation failed to block progression")
                return False
            
            # Fill only project title, leave deadline empty
            project_title = self.driver.find_element(By.ID, "project_title")
            project_title.send_keys("Test Project")
            next_button.click()
            time.sleep(1)
            
            # Get console logs
            print("Console logs after partial form Next click:")
            self.get_console_logs()
            
            # Should still be on step 1
            try:
                step1 = self.driver.find_element(By.CSS_SELECTOR, '[data-step="1"].active')
                print("✅ GOOD: Validation blocked progression with missing deadline")
            except NoSuchElementException:
                print("❌ BAD: Validation failed to block with missing deadline")
                return False
            
            print("✅ Validation blocking works correctly!")
            return True
            
        except Exception as e:
            print(f"❌ Validation test failed: {e}")
            self.get_console_logs()
            return False

def main():
    """Main test function"""
    test = OnboardingSeleniumTest()
    
    try:
        # Start the server
        test.start_server()
        
        # Setup WebDriver
        test.setup_driver()
        
        # Run the tests
        print("="*60)
        print("ONBOARDING SELENIUM TEST")
        print("="*60)
        
        # Test normal flow
        flow_success = test.test_onboarding_flow()
        
        # Test validation
        validation_success = test.test_validation_blocking()
        
        print("\n" + "="*60)
        print("TEST RESULTS")
        print("="*60)
        print(f"Onboarding Flow: {'✅ PASS' if flow_success else '❌ FAIL'}")
        print(f"Validation Blocking: {'✅ PASS' if validation_success else '❌ FAIL'}")
        
        if flow_success and validation_success:
            print("\n🎉 ALL TESTS PASSED! The onboarding Next button is working correctly!")
        else:
            print("\n❌ Some tests failed. Check the output above for details.")
            
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Test failed with error: {e}")
    finally:
        # Cleanup
        test.cleanup_driver()
        test.stop_server()

if __name__ == "__main__":
    main()