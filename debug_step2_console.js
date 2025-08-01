// Debug Step 2 Research Phases Visibility
// Copy and paste this into your browser console when on the onboarding page

console.log('=== STEP 2 DEBUG DIAGNOSTICS ===');

// Check if we're on step 2
const currentStep = document.querySelector('.step-content.active');
if (currentStep) {
    const stepNumber = currentStep.getAttribute('data-step');
    console.log('Current active step:', stepNumber);
    
    if (stepNumber === '2') {
        console.log('✅ Currently on Step 2');
        
        // Check if phases-grid exists
        const phasesGrid = document.querySelector('.phases-grid');
        console.log('Phases grid element:', phasesGrid);
        
        if (phasesGrid) {
            console.log('✅ Phases grid found');
            
            // Check computed styles
            const gridStyles = window.getComputedStyle(phasesGrid);
            console.log('Phases grid styles:', {
                display: gridStyles.display,
                visibility: gridStyles.visibility,
                opacity: gridStyles.opacity,
                height: gridStyles.height,
                width: gridStyles.width,
                overflow: gridStyles.overflow
            });
            
            // Check phase toggles
            const phaseToggles = phasesGrid.querySelectorAll('.phase-toggle');
            console.log(`Found ${phaseToggles.length} phase toggles`);
            
            phaseToggles.forEach((toggle, index) => {
                const styles = window.getComputedStyle(toggle);
                const phase = toggle.getAttribute('data-phase');
                console.log(`Phase ${index + 1} (${phase}):`, {
                    display: styles.display,
                    visibility: styles.visibility,
                    height: styles.height,
                    borderColor: styles.borderColor,
                    backgroundColor: styles.backgroundColor
                });
                
                // Check if phase content is visible
                const phaseCard = toggle.querySelector('.phase-card');
                const phaseContent = toggle.querySelector('.phase-content');
                if (phaseCard && phaseContent) {
                    const cardStyles = window.getComputedStyle(phaseCard);
                    const contentStyles = window.getComputedStyle(phaseContent);
                    console.log(`  Phase card styles:`, {
                        display: cardStyles.display,
                        visibility: cardStyles.visibility
                    });
                    console.log(`  Phase content styles:`, {
                        display: contentStyles.display,
                        visibility: contentStyles.visibility
                    });
                }
            });
            
        } else {
            console.log('❌ Phases grid NOT found');
        }
        
    } else {
        console.log(`❌ Not on Step 2, currently on step ${stepNumber}`);
        console.log('To go to Step 2, try: goToStep2()');
        
        // Define helper function
        window.goToStep2 = function() {
            // Hide all steps
            document.querySelectorAll('.step-content').forEach(step => {
                step.classList.remove('active');
            });
            
            // Show step 2
            const step2 = document.querySelector('[data-step="2"]');
            if (step2) {
                step2.classList.add('active');
                console.log('Manually activated Step 2');
                
                // Re-run diagnostics
                setTimeout(() => {
                    console.log('Re-running diagnostics after manual activation...');
                    eval(document.querySelector('script[src*="debug_step2_console"]')?.textContent || '');
                }, 100);
            } else {
                console.log('❌ Could not find Step 2 element');
            }
        };
    }
    
} else {
    console.log('❌ No active step found');
}

// Check if OnboardingWizard exists
if (window.OnboardingWizard || window.wizard) {
    console.log('✅ OnboardingWizard class available');
    
    // Try to get current wizard instance
    const wizard = window.wizard || new OnboardingWizard();
    console.log('Wizard current step:', wizard.currentStep);
    
    // Define helper to advance to step 2
    window.advanceToStep2 = function() {
        // Fill step 1 requirements
        const projectTitle = document.getElementById('project_title');
        const thesisDeadline = document.getElementById('thesis_deadline');
        
        if (projectTitle && !projectTitle.value) {
            projectTitle.value = 'Test Research Project';
            console.log('Filled project title');
        }
        
        if (thesisDeadline && !thesisDeadline.value) {
            const futureDate = new Date();
            futureDate.setDate(futureDate.getDate() + 90);
            thesisDeadline.value = futureDate.toISOString().split('T')[0];
            console.log('Filled thesis deadline');
        }
        
        // Try to advance
        wizard.nextStep();
        console.log('Called nextStep(), new current step:', wizard.currentStep);
    };
    
} else {
    console.log('❌ OnboardingWizard not available');
}

// Check CSS loading
const modernCSS = document.querySelector('link[href*="modern.css"]');
console.log('Modern CSS loaded:', !!modernCSS);

if (modernCSS) {
    console.log('CSS href:', modernCSS.href);
}

// Check for any CSS that might hide phases
const allStyles = Array.from(document.styleSheets);
console.log(`Found ${allStyles.length} stylesheets`);

console.log('=== END DIAGNOSTICS ===');
console.log('Available helper functions:');
console.log('- goToStep2() - manually go to step 2');
console.log('- advanceToStep2() - fill step 1 and advance');