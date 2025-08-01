#!/usr/bin/env python3
"""
Analyze the onboarding JavaScript for issues
"""

import re
import json

def analyze_onboarding_js():
    """Analyze the JavaScript in the onboarding template"""
    
    print("="*60)
    print("ONBOARDING JAVASCRIPT ANALYSIS")
    print("="*60)
    
    # Read the onboard template
    with open('templates/onboard.html', 'r') as f:
        content = f.read()
    
    # Extract JavaScript section
    js_start = content.find('<script>')
    js_end = content.find('</script>')
    
    if js_start == -1 or js_end == -1:
        print("❌ No JavaScript section found")
        return False
    
    js_content = content[js_start + 8:js_end]  # +8 to skip '<script>'
    
    print("✓ JavaScript section found")
    print(f"JavaScript length: {len(js_content)} characters")
    
    # Check for basic syntax issues
    issues = []
    
    # 1. Check for duplicate method definitions
    methods = ['nextStep', 'prevStep', 'updateStep', 'validateCurrentStep', 'updateReview', 'initPresets', 'getPhaseDisplayName']
    
    print("\n--- Method Definition Analysis ---")
    for method in methods:
        pattern = f'{method}\\(\\)\\s*\\{{'
        matches = re.findall(pattern, js_content)
        count = len(matches)
        
        if count == 1:
            print(f"✓ {method}(): {count} definition")
        elif count == 0:
            print(f"❌ {method}(): {count} definitions (MISSING)")
            issues.append(f"Missing method: {method}")
        else:
            print(f"❌ {method}(): {count} definitions (DUPLICATE)")
            issues.append(f"Duplicate method: {method}")
    
    # 2. Check for class structure
    print("\n--- Class Structure Analysis ---")
    
    if 'class OnboardingWizard {' in js_content:
        print("✓ OnboardingWizard class defined")
    else:
        print("❌ OnboardingWizard class not found")
        issues.append("Missing OnboardingWizard class")
    
    if 'new OnboardingWizard()' in js_content:
        print("✓ OnboardingWizard instantiated")
    else:
        print("❌ OnboardingWizard not instantiated")
        issues.append("OnboardingWizard not instantiated")
    
    # 3. Check for event binding
    print("\n--- Event Binding Analysis ---")
    
    if "addEventListener('click', () => this.nextStep())" in js_content:
        print("✓ Next button event listener bound")
    else:
        print("❌ Next button event listener not found")
        issues.append("Next button event listener missing")
    
    # 4. Check for specific syntax errors
    print("\n--- Syntax Error Analysis ---")
    
    # Check for malformed getPhaseDisplayName
    if 'deadline.style.display' in js_content and 'getPhaseDisplayName' in js_content:
        # Find the getPhaseDisplayName method
        method_start = js_content.find('getPhaseDisplayName(phaseType) {')
        if method_start != -1:
            method_end = js_content.find('}', method_start)
            method_content = js_content[method_start:method_end + 1]
            
            if 'deadline.style.display' in method_content:
                print("❌ getPhaseDisplayName contains invalid syntax")
                issues.append("getPhaseDisplayName method has invalid syntax")
            else:
                print("✓ getPhaseDisplayName looks correct")
        else:
            print("❌ getPhaseDisplayName method not found")
            issues.append("getPhaseDisplayName method missing")
    else:
        print("✓ No obvious syntax errors in getPhaseDisplayName")
    
    # 5. Check for balanced braces
    print("\n--- Brace Balance Analysis ---")
    
    open_braces = js_content.count('{')
    close_braces = js_content.count('}')
    
    if open_braces == close_braces:
        print(f"✓ Braces balanced: {open_braces} open, {close_braces} close")
    else:
        print(f"❌ Braces unbalanced: {open_braces} open, {close_braces} close")
        issues.append(f"Unbalanced braces: {open_braces} open, {close_braces} close")
    
    # 6. Check for console.log statements (debug logging)
    print("\n--- Debug Logging Analysis ---")
    
    console_logs = js_content.count('console.log')
    if console_logs > 0:
        print(f"✓ Debug logging present: {console_logs} console.log statements")
    else:
        print("⚠️  No debug logging found")
    
    # 7. Look for specific validation issues
    print("\n--- Validation Logic Analysis ---")
    
    if 'validateCurrentStep()' in js_content:
        print("✓ validateCurrentStep method exists")
        
        # Check if validation has proper return statements
        if 'return false' in js_content and 'return true' in js_content:
            print("✓ Validation has return statements")
        else:
            print("❌ Validation missing proper return statements")
            issues.append("Validation logic incomplete")
    else:
        print("❌ validateCurrentStep method missing")
        issues.append("validateCurrentStep method missing")
    
    # 8. Check for DOM element access
    print("\n--- DOM Access Analysis ---")
    
    dom_methods = ['getElementById', 'querySelector', 'querySelectorAll']
    for method in dom_methods:
        if method in js_content:
            print(f"✓ Uses {method}")
        else:
            print(f"⚠️  Does not use {method}")
    
    # Summary
    print("\n" + "="*60)
    print("ANALYSIS SUMMARY")
    print("="*60)
    
    if not issues:
        print("✅ No major issues found in JavaScript!")
        print("The Next button should work correctly.")
        return True
    else:
        print(f"❌ Found {len(issues)} issues:")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
        
        print("\nRecommended fixes:")
        if any("Duplicate method" in issue for issue in issues):
            print("  - Remove duplicate method definitions")
        if any("Missing method" in issue for issue in issues):
            print("  - Add missing method definitions")
        if any("syntax" in issue.lower() for issue in issues):
            print("  - Fix JavaScript syntax errors")
        if any("event listener" in issue.lower() for issue in issues):
            print("  - Fix event binding")
        
        return False

def extract_and_test_js():
    """Extract JavaScript and create a test file"""
    
    print("\n--- Creating JavaScript Test File ---")
    
    # Read the onboard template
    with open('templates/onboard.html', 'r') as f:
        content = f.read()
    
    # Extract JavaScript section
    js_start = content.find('<script>')
    js_end = content.find('</script>')
    
    if js_start == -1 or js_end == -1:
        print("❌ No JavaScript section found")
        return
    
    js_content = content[js_start + 8:js_end]
    
    # Create a test HTML file with the JavaScript
    test_html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>JavaScript Test</title>
</head>
<body>
    <div id="test-results"></div>
    
    <!-- Mock DOM elements -->
    <div style="display: none;">
        <form id="onboarding-form">
            <div class="step-content active" data-step="1">
                <input type="text" id="project_title" required>
                <input type="date" id="thesis_deadline" required>
            </div>
            <div class="step-content" data-step="2">
                <input type="checkbox" name="selected_phases" value="literature_review" checked>
                <input type="date" name="literature_review_deadline" required>
            </div>
            <div class="step-content" data-step="3"></div>
            <div class="step-content" data-step="4">
                <div id="review-title"></div>
                <div id="review-deadline"></div>
                <div id="review-phases"></div>
                <div id="review-schedule"></div>
            </div>
        </form>
        
        <div id="progress-fill"></div>
        <button id="next-btn">Next</button>
        <button id="prev-btn">Previous</button>
        <button id="submit-btn">Submit</button>
    </div>

    <script>
    // Test runner
    function runTests() {{
        const results = document.getElementById('test-results');
        
        try {{
            // Test 1: Can we instantiate the class?
            console.log('Test 1: Instantiating OnboardingWizard');
            const wizard = new OnboardingWizard();
            results.innerHTML += '<div>✅ OnboardingWizard instantiated successfully</div>';
            
            // Test 2: Does nextStep method exist?
            if (typeof wizard.nextStep === 'function') {{
                results.innerHTML += '<div>✅ nextStep method exists</div>';
            }} else {{
                results.innerHTML += '<div>❌ nextStep method missing</div>';
            }}
            
            // Test 3: Does validateCurrentStep method exist?
            if (typeof wizard.validateCurrentStep === 'function') {{
                results.innerHTML += '<div>✅ validateCurrentStep method exists</div>';
            }} else {{
                results.innerHTML += '<div>❌ validateCurrentStep method missing</div>';
            }}
            
            // Test 4: Can we call nextStep?
            try {{
                // Fill required fields first
                document.getElementById('project_title').value = 'Test Project';
                document.getElementById('thesis_deadline').value = '2025-12-31';
                
                const initialStep = wizard.currentStep;
                wizard.nextStep();
                const newStep = wizard.currentStep;
                
                if (newStep > initialStep) {{
                    results.innerHTML += '<div>✅ nextStep() advances steps</div>';
                }} else {{
                    results.innerHTML += '<div>❌ nextStep() does not advance steps</div>';
                }}
            }} catch (e) {{
                results.innerHTML += '<div>❌ nextStep() threw error: ' + e.message + '</div>';
            }}
            
        }} catch (e) {{
            results.innerHTML += '<div>❌ Failed to instantiate OnboardingWizard: ' + e.message + '</div>';
            console.error('Error:', e);
        }}
    }}
    
    {js_content}
    
    // Run tests when page loads
    document.addEventListener('DOMContentLoaded', runTests);
    </script>
</body>
</html>
"""
    
    # Write the test file
    with open('test_js_functionality.html', 'w') as f:
        f.write(test_html)
    
    print("✓ Created test_js_functionality.html")
    print("Open this file in a browser to test JavaScript functionality")

if __name__ == "__main__":
    success = analyze_onboarding_js()
    extract_and_test_js()
    
    if not success:
        print("\n🔧 NEXT STEPS:")
        print("1. Open test_js_functionality.html in a browser")
        print("2. Check the browser console for JavaScript errors")
        print("3. Look at the test results on the page")
        print("4. Fix any issues found in the analysis above")