#!/usr/bin/env python3
"""
Direct test of onboarding HTML without Flask server
"""

import sys
import os
import time
from datetime import datetime, timedelta

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
except ImportError:
    print("Selenium not available")
    sys.exit(1)

def create_test_html():
    """Create a standalone test HTML file"""
    
    # Read the onboard template
    with open('templates/onboard.html', 'r') as f:
        template_content = f.read()
    
    # Extract just the content between {% block content %} and {% endblock %}
    start_marker = '{% block content %}'
    end_marker = '{% endblock %}'
    
    start_idx = template_content.find(start_marker)
    end_idx = template_content.find(end_marker)
    
    if start_idx == -1 or end_idx == -1:
        print("Could not find content blocks in template")
        return None
    
    content = template_content[start_idx + len(start_marker):end_idx]
    
    # Replace Flask template variables with static values
    content = content.replace("{{ url_for('submit_onboarding') }}", "#")
    
    # Create a complete HTML document
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Onboarding Test</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        /* Basic styling for the test */
        body {{ font-family: 'Inter', sans-serif; margin: 0; padding: 20px; background: #f8fafc; }}
        .onboarding-container {{ max-width: 800px; margin: 0 auto; background: white; border-radius: 12px; padding: 40px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        .progress-container {{ margin-bottom: 40px; }}
        .progress-bar {{ width: 100%; height: 8px; background: #e5e7eb; border-radius: 4px; overflow: hidden; }}
        .progress-fill {{ height: 100%; background: #3b82f6; transition: width 0.3s ease; }}
        .progress-steps {{ display: flex; justify-content: space-between; margin-top: 16px; }}
        .step {{ display: flex; flex-direction: column; align-items: center; }}
        .step-circle {{ width: 32px; height: 32px; border-radius: 50%; background: #e5e7eb; display: flex; align-items: center; justify-content: center; font-weight: 600; color: #6b7280; }}
        .step.active .step-circle {{ background: #3b82f6; color: white; }}
        .step-label {{ font-size: 12px; margin-top: 8px; color: #6b7280; }}
        .step.active .step-label {{ color: #3b82f6; }}
        .step-content {{ display: none; }}
        .step-content.active {{ display: block; }}
        .step-header {{ margin-bottom: 32px; }}
        .step-header h2 {{ font-size: 24px; font-weight: 600; color: #1f2937; margin: 0 0 8px 0; }}
        .step-header p {{ color: #6b7280; margin: 0; }}
        .form-card {{ background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; padding: 24px; }}
        .form-group {{ margin-bottom: 20px; }}
        .form-group label {{ display: block; font-weight: 500; color: #374151; margin-bottom: 6px; }}
        .form-group input {{ width: 100%; padding: 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 16px; }}
        .form-group input:focus {{ outline: none; border-color: #3b82f6; box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1); }}
        .input-hint {{ font-size: 14px; color: #6b7280; margin-top: 4px; }}
        .phase-toggle {{ margin: 16px 0; border: 2px solid #e5e7eb; border-radius: 8px; padding: 16px; cursor: pointer; }}
        .phase-toggle.active {{ border-color: #3b82f6; background: #eff6ff; }}
        .phase-card {{ cursor: pointer; }}
        .phase-card h3 {{ margin: 0 0 8px 0; font-size: 18px; }}
        .phase-card p {{ margin: 0; color: #6b7280; }}
        .phase-deadline {{ display: none; margin-top: 16px; }}
        .phase-deadline label {{ font-weight: 500; }}
        .phase-deadline input {{ width: 200px; }}
        .step-navigation {{ display: flex; justify-content: space-between; margin-top: 40px; }}
        .btn-primary {{ background: #3b82f6; color: white; padding: 12px 24px; border: none; border-radius: 6px; font-weight: 500; cursor: pointer; display: flex; align-items: center; gap: 8px; }}
        .btn-primary:hover {{ background: #2563eb; }}
        .btn-secondary {{ background: #6b7280; color: white; padding: 12px 24px; border: none; border-radius: 6px; font-weight: 500; cursor: pointer; display: flex; align-items: center; gap: 8px; }}
        .btn-secondary:hover {{ background: #4b5563; }}
        .days-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 16px; }}
        .day-card {{ border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px; }}
        .day-header {{ margin-bottom: 12px; }}
        .day-name {{ font-weight: 500; }}
        .intensity-selector {{ display: flex; gap: 8px; }}
        .intensity-option {{ display: flex; align-items: center; gap: 4px; cursor: pointer; }}
        .review-item {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #e5e7eb; }}
        .review-label {{ font-weight: 500; }}
        .review-value {{ color: #6b7280; }}
    </style>
</head>
<body>
{content}
</body>
</html>
"""
    
    # Write the test file
    with open('test_onboarding_standalone.html', 'w') as f:
        f.write(html_content)
    
    return os.path.abspath('test_onboarding_standalone.html')

def test_onboarding_standalone():
    """Test the onboarding functionality using the standalone HTML file"""
    
    # Create the test HTML file
    html_file = create_test_html()
    if not html_file:
        print("Failed to create test HTML file")
        return False
    
    print(f"Created test file: {html_file}")
    
    # Setup Chrome WebDriver
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Comment out to see browser
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1200,800")
    
    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(5)
        print("✓ Chrome WebDriver initialized")
        
        # Load the HTML file
        driver.get(f"file://{html_file}")
        print("✓ HTML file loaded")
        
        # Enable console logging
        def get_console_logs():
            try:
                logs = driver.get_log('browser')
                for log in logs:
                    if log['level'] in ['SEVERE', 'WARNING']:
                        print(f"BROWSER {log['level']}: {log['message']}")
            except Exception as e:
                pass
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "onboarding-form"))
        )
        print("✓ Onboarding form found")
        
        # Check if we're on step 1
        step1 = driver.find_element(By.CSS_SELECTOR, '[data-step="1"].active')
        if step1:
            print("✓ Currently on Step 1")
        else:
            print("✗ Not on Step 1")
            return False
        
        # Test Step 1: Fill out project information
        print("\n--- Testing Step 1 ---")
        
        # Fill project title
        project_title = driver.find_element(By.ID, "project_title")
        project_title.clear()
        project_title.send_keys("Test Research Project")
        print("✓ Filled project title")
        
        # Fill thesis deadline (90 days from now)
        future_date = (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d")
        thesis_deadline = driver.find_element(By.ID, "thesis_deadline")
        thesis_deadline.clear()
        thesis_deadline.send_keys(future_date)
        print(f"✓ Filled thesis deadline: {future_date}")
        
        # Get console logs before clicking
        print("Checking for JavaScript errors...")
        get_console_logs()
        
        # Click Next button
        print("Clicking Next button...")
        next_button = driver.find_element(By.ID, "next-btn")
        
        # Execute JavaScript to see what happens
        driver.execute_script("console.log('About to click Next button');")
        next_button.click()
        driver.execute_script("console.log('Next button clicked');")
        
        print("✓ Next button clicked")
        
        # Wait a moment for transition
        time.sleep(3)
        
        # Get console logs after clicking
        print("Console logs after clicking Next:")
        get_console_logs()
        
        # Check if we advanced to step 2
        try:
            step2 = driver.find_element(By.CSS_SELECTOR, '[data-step="2"].active')
            print("✅ SUCCESS: Advanced to Step 2!")
            return True
        except NoSuchElementException:
            print("❌ FAILED: Still on Step 1")
            
            # Check what step we're actually on
            for i in range(1, 5):
                try:
                    step = driver.find_element(By.CSS_SELECTOR, f'[data-step="{i}"].active')
                    print(f"Currently on step: {i}")
                    break
                except NoSuchElementException:
                    continue
            
            # Try to debug what's happening
            print("Debugging information:")
            
            # Check if the Next button is visible and enabled
            next_btn = driver.find_element(By.ID, "next-btn")
            print(f"Next button visible: {next_btn.is_displayed()}")
            print(f"Next button enabled: {next_btn.is_enabled()}")
            
            # Check form validation
            form_valid = driver.execute_script("return document.getElementById('onboarding-form').checkValidity();")
            print(f"Form valid: {form_valid}")
            
            # Check individual field validity
            title_valid = driver.execute_script("return document.getElementById('project_title').checkValidity();")
            deadline_valid = driver.execute_script("return document.getElementById('thesis_deadline').checkValidity();")
            print(f"Title valid: {title_valid}, Deadline valid: {deadline_valid}")
            
            # Try to manually trigger the nextStep function
            print("Trying to manually call nextStep()...")
            result = driver.execute_script("""
                if (window.wizard) {
                    console.log('Wizard found, calling nextStep()');
                    window.wizard.nextStep();
                    return 'nextStep called';
                } else {
                    console.log('No wizard found');
                    return 'no wizard';
                }
            """)
            print(f"Manual nextStep result: {result}")
            
            time.sleep(2)
            get_console_logs()
            
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        if driver:
            get_console_logs()
        return False
    finally:
        if driver:
            driver.quit()
            print("WebDriver closed")
        
        # Clean up test file
        if os.path.exists('test_onboarding_standalone.html'):
            os.remove('test_onboarding_standalone.html')

if __name__ == "__main__":
    print("="*60)
    print("ONBOARDING STANDALONE TEST")
    print("="*60)
    
    success = test_onboarding_standalone()
    
    print("\n" + "="*60)
    print("TEST RESULTS")
    print("="*60)
    
    if success:
        print("✅ SUCCESS: Onboarding Next button works!")
    else:
        print("❌ FAILED: Onboarding Next button has issues")
        print("\nThis test helps identify if the issue is:")
        print("1. JavaScript errors preventing execution")
        print("2. Validation logic blocking progression")
        print("3. Event binding problems")
        print("4. Step transition logic issues")