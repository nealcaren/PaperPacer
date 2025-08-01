#!/usr/bin/env python3
"""
Playwright test for onboarding Next button functionality
"""

import asyncio
import sys
import os
from playwright.async_api import async_playwright
import subprocess
import time
import signal

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class OnboardingTest:
    def __init__(self):
        self.server_process = None
        self.base_url = "http://localhost:5001"
        
    async def start_server(self):
        """Start the Flask development server"""
        print("Starting Flask server...")
        self.server_process = subprocess.Popen([
            sys.executable, "-c", 
            """
import sys
import os
sys.path.append('.')
from app import app
app.run(debug=False, port=5001, host='127.0.0.1')
            """
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for server to start
        await asyncio.sleep(3)
        print("Flask server started on port 5001")
        
    def stop_server(self):
        """Stop the Flask server"""
        if self.server_process:
            self.server_process.terminate()
            self.server_process.wait()
            print("Flask server stopped")
    
    async def test_onboarding_flow(self):
        """Test the complete onboarding flow"""
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(headless=False, slow_mo=1000)  # Visible browser with slow motion
            context = await browser.new_context()
            page = await context.new_page()
            
            # Enable console logging
            page.on("console", lambda msg: print(f"BROWSER CONSOLE: {msg.text}"))
            page.on("pageerror", lambda error: print(f"BROWSER ERROR: {error}"))
            
            try:
                print(f"Navigating to {self.base_url}/onboard")
                await page.goto(f"{self.base_url}/onboard")
                
                # Wait for page to load
                await page.wait_for_selector("#onboarding-form", timeout=10000)
                print("✓ Onboarding page loaded")
                
                # Check if we're on step 1
                step1 = await page.query_selector('[data-step="1"].active')
                if step1:
                    print("✓ Currently on Step 1")
                else:
                    print("✗ Not on Step 1")
                    return False
                
                # Test Step 1: Fill out project information
                print("\n--- Testing Step 1 ---")
                
                # Fill project title
                await page.fill("#project_title", "Test Research Project")
                print("✓ Filled project title")
                
                # Fill thesis deadline (90 days from now)
                import datetime
                future_date = (datetime.datetime.now() + datetime.timedelta(days=90)).strftime("%Y-%m-%d")
                await page.fill("#thesis_deadline", future_date)
                print(f"✓ Filled thesis deadline: {future_date}")
                
                # Click Next button
                print("Clicking Next button...")
                next_button = await page.query_selector("#next-btn")
                if next_button:
                    await next_button.click()
                    print("✓ Next button clicked")
                    
                    # Wait a moment for transition
                    await asyncio.sleep(2)
                    
                    # Check if we advanced to step 2
                    step2 = await page.query_selector('[data-step="2"].active')
                    if step2:
                        print("✅ SUCCESS: Advanced to Step 2!")
                    else:
                        print("❌ FAILED: Still on Step 1")
                        # Check what step we're actually on
                        for i in range(1, 5):
                            step = await page.query_selector(f'[data-step="{i}"].active')
                            if step:
                                print(f"Currently on step: {i}")
                                break
                        return False
                else:
                    print("✗ Next button not found")
                    return False
                
                # Test Step 2: Research Phases
                print("\n--- Testing Step 2 ---")
                
                # Check if literature review is already selected (it should be by default)
                lit_review_checked = await page.is_checked("#phase_literature_review")
                print(f"Literature review checked: {lit_review_checked}")
                
                if lit_review_checked:
                    # Fill the deadline for literature review
                    deadline_date = (datetime.datetime.now() + datetime.timedelta(days=30)).strftime("%Y-%m-%d")
                    await page.fill("#literature_review_deadline", deadline_date)
                    print(f"✓ Filled literature review deadline: {deadline_date}")
                else:
                    # Check the literature review checkbox
                    await page.check("#phase_literature_review")
                    print("✓ Checked literature review")
                    
                    # Fill the deadline
                    deadline_date = (datetime.datetime.now() + datetime.timedelta(days=30)).strftime("%Y-%m-%d")
                    await page.fill("#literature_review_deadline", deadline_date)
                    print(f"✓ Filled literature review deadline: {deadline_date}")
                
                # Click Next button for step 2
                print("Clicking Next button for Step 2...")
                await next_button.click()
                await asyncio.sleep(2)
                
                # Check if we advanced to step 3
                step3 = await page.query_selector('[data-step="3"].active')
                if step3:
                    print("✅ SUCCESS: Advanced to Step 3!")
                else:
                    print("❌ FAILED: Could not advance from Step 2")
                    # Check current step
                    for i in range(1, 5):
                        step = await page.query_selector(f'[data-step="{i}"].active')
                        if step:
                            print(f"Currently on step: {i}")
                            break
                    return False
                
                # Test Step 3: Work Schedule
                print("\n--- Testing Step 3 ---")
                
                # Select some work days
                await page.check('input[name="monday_intensity"][value="light"]')
                await page.check('input[name="tuesday_intensity"][value="heavy"]')
                print("✓ Selected work schedule")
                
                # Click Next button for step 3
                print("Clicking Next button for Step 3...")
                await next_button.click()
                await asyncio.sleep(2)
                
                # Check if we advanced to step 4
                step4 = await page.query_selector('[data-step="4"].active')
                if step4:
                    print("✅ SUCCESS: Advanced to Step 4!")
                    
                    # Check if submit button is visible
                    submit_button = await page.query_selector("#submit-btn")
                    if submit_button:
                        is_visible = await submit_button.is_visible()
                        print(f"✓ Submit button visible: {is_visible}")
                    else:
                        print("✗ Submit button not found")
                        
                else:
                    print("❌ FAILED: Could not advance from Step 3")
                    return False
                
                print("\n🎉 ALL TESTS PASSED! Onboarding flow works correctly!")
                return True
                
            except Exception as e:
                print(f"❌ Test failed with error: {e}")
                return False
            finally:
                await browser.close()
    
    async def test_validation_blocking(self):
        """Test that validation properly blocks progression"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False, slow_mo=500)
            context = await browser.new_context()
            page = await context.new_page()
            
            # Enable console logging
            page.on("console", lambda msg: print(f"VALIDATION TEST CONSOLE: {msg.text}"))
            
            try:
                print(f"\n--- Testing Validation Blocking ---")
                await page.goto(f"{self.base_url}/onboard")
                await page.wait_for_selector("#onboarding-form", timeout=10000)
                
                # Try to click Next without filling anything
                print("Trying to advance without filling required fields...")
                next_button = await page.query_selector("#next-btn")
                await next_button.click()
                await asyncio.sleep(1)
                
                # Should still be on step 1
                step1 = await page.query_selector('[data-step="1"].active')
                if step1:
                    print("✅ GOOD: Validation blocked progression (still on Step 1)")
                else:
                    print("❌ BAD: Validation failed to block progression")
                    return False
                
                # Fill only project title, leave deadline empty
                await page.fill("#project_title", "Test Project")
                await next_button.click()
                await asyncio.sleep(1)
                
                # Should still be on step 1
                step1 = await page.query_selector('[data-step="1"].active')
                if step1:
                    print("✅ GOOD: Validation blocked progression with missing deadline")
                else:
                    print("❌ BAD: Validation failed to block with missing deadline")
                    return False
                
                print("✅ Validation blocking works correctly!")
                return True
                
            except Exception as e:
                print(f"❌ Validation test failed: {e}")
                return False
            finally:
                await browser.close()

async def main():
    """Main test function"""
    test = OnboardingTest()
    
    try:
        # Start the server
        await test.start_server()
        
        # Run the tests
        print("="*60)
        print("ONBOARDING PLAYWRIGHT TEST")
        print("="*60)
        
        # Test normal flow
        flow_success = await test.test_onboarding_flow()
        
        # Test validation
        validation_success = await test.test_validation_blocking()
        
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
        # Stop the server
        test.stop_server()

if __name__ == "__main__":
    # Check if playwright is installed
    try:
        import playwright
    except ImportError:
        print("Playwright not installed. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "playwright"])
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])
        print("Playwright installed. Please run the test again.")
        sys.exit(1)
    
    asyncio.run(main())