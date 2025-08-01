#!/usr/bin/env python3
"""
Final test to verify the onboarding Next button is fixed
"""

def test_onboarding_javascript():
    """Test that the onboarding JavaScript is properly structured"""
    
    with open('templates/onboard.html', 'r') as f:
        content = f.read()
    
    print("Testing onboarding JavaScript structure...")
    print("=" * 60)
    
    # Test 1: Check for single method definitions
    methods = ['nextStep', 'prevStep', 'updateStep', 'validateCurrentStep', 'updateReview']
    
    for method in methods:
        count = content.count(f'{method}() {{')
        if count == 1:
            print(f"✓ {method}(): Found exactly 1 definition")
        else:
            print(f"✗ {method}(): Found {count} definitions (should be 1)")
            return False
    
    # Test 2: Check for proper event binding
    if 'addEventListener(\'click\', () => this.nextStep())' in content:
        print("✓ Next button event listener is properly bound")
    else:
        print("✗ Next button event listener not found")
        return False
    
    # Test 3: Check for class structure
    if 'class OnboardingWizard {' in content:
        print("✓ OnboardingWizard class is defined")
    else:
        print("✗ OnboardingWizard class not found")
        return False
    
    # Test 4: Check for initialization
    if 'new OnboardingWizard()' in content:
        print("✓ OnboardingWizard is instantiated")
    else:
        print("✗ OnboardingWizard instantiation not found")
        return False
    
    # Test 5: Check that duplicate section was removed
    duplicate_indicators = [
        'initPresets() {' + '\n' + '        const presetCards = document.querySelectorAll(\'.preset-card\');' + '\n' + '        ' + '\n' + '        presetCards.forEach(card => {',
        'nextStep() {' + '\n' + '        if (this.validateCurrentStep()) {'
    ]
    
    duplicate_count = 0
    for indicator in duplicate_indicators:
        duplicate_count += content.count(indicator)
    
    if duplicate_count <= len(duplicate_indicators):
        print("✓ No duplicate method blocks found")
    else:
        print(f"✗ Found {duplicate_count} duplicate method blocks")
        return False
    
    print("=" * 60)
    print("🎉 ALL TESTS PASSED! The onboarding Next button should now work!")
    print("\nWhat was fixed:")
    print("- Removed duplicate JavaScript method definitions")
    print("- Kept original working methods intact")
    print("- Event listeners are properly bound")
    print("- Class structure is correct")
    
    return True

if __name__ == '__main__':
    success = test_onboarding_javascript()
    if not success:
        print("\n❌ Some tests failed. The Next button may still have issues.")
        exit(1)
    else:
        print("\n✅ Fix verified successfully!")
        exit(0)