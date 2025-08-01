// Fix for Step 2 Research Phases visibility issue
// This script ensures Step 2 content is properly displayed

(function() {
    'use strict';
    
    console.log('🔧 Applying Step 2 visibility fix...');
    
    // Function to ensure Step 2 is properly styled and visible
    function fixStep2Visibility() {
        // Add CSS to ensure phases are visible
        const style = document.createElement('style');
        style.textContent = `
            /* Ensure Step 2 content is visible */
            .step-content[data-step="2"] {
                display: block !important;
            }
            
            .step-content[data-step="2"].active {
                display: block !important;
                visibility: visible !important;
                opacity: 1 !important;
            }
            
            /* Ensure phases grid is visible */
            .phases-grid {
                display: grid !important;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)) !important;
                gap: 16px !important;
                margin: 20px 0 !important;
            }
            
            /* Ensure phase toggles are visible */
            .phase-toggle {
                display: block !important;
                visibility: visible !important;
                opacity: 1 !important;
                border: 2px solid #e5e7eb !important;
                border-radius: 8px !important;
                padding: 16px !important;
                margin-bottom: 16px !important;
                background: white !important;
            }
            
            .phase-toggle.active {
                border-color: #3b82f6 !important;
                background: #eff6ff !important;
            }
            
            /* Ensure phase cards are visible */
            .phase-card {
                display: block !important;
                cursor: pointer !important;
            }
            
            .phase-content {
                display: block !important;
            }
            
            .phase-content h3 {
                margin: 8px 0 !important;
                font-size: 18px !important;
                font-weight: 600 !important;
            }
            
            .phase-content p {
                margin: 4px 0 !important;
                color: #6b7280 !important;
            }
            
            .phase-icon {
                font-size: 24px !important;
                margin-bottom: 8px !important;
                display: block !important;
            }
            
            /* Ensure phase deadlines work */
            .phase-deadline {
                margin-top: 12px !important;
                padding-top: 12px !important;
                border-top: 1px solid #e5e7eb !important;
            }
            
            .phase-deadline input {
                width: 100% !important;
                max-width: 200px !important;
                padding: 8px !important;
                border: 1px solid #d1d5db !important;
                border-radius: 6px !important;
            }
            
            /* Debug: Add red border to help identify issues */
            .debug-step2 .phases-grid {
                border: 2px solid red !important;
            }
            
            .debug-step2 .phase-toggle {
                border: 2px solid blue !important;
            }
        `;
        document.head.appendChild(style);
        console.log('✅ Added Step 2 visibility CSS');
    }
    
    // Function to force Step 2 to be visible
    function forceStep2Visible() {
        const step2 = document.querySelector('[data-step="2"]');
        if (step2) {
            step2.style.display = 'block';
            step2.style.visibility = 'visible';
            step2.style.opacity = '1';
            console.log('✅ Forced Step 2 to be visible');
        }
        
        const phasesGrid = document.querySelector('.phases-grid');
        if (phasesGrid) {
            phasesGrid.style.display = 'grid';
            phasesGrid.style.visibility = 'visible';
            phasesGrid.style.opacity = '1';
            console.log('✅ Forced phases grid to be visible');
        }
        
        const phaseToggles = document.querySelectorAll('.phase-toggle');
        phaseToggles.forEach((toggle, index) => {
            toggle.style.display = 'block';
            toggle.style.visibility = 'visible';
            toggle.style.opacity = '1';
            console.log(`✅ Forced phase toggle ${index + 1} to be visible`);
        });
    }
    
    // Function to reinitialize phase toggles
    function reinitializePhaseToggles() {
        const phaseToggles = document.querySelectorAll('.phase-toggle');
        
        phaseToggles.forEach(toggle => {
            const checkbox = toggle.querySelector('input[type="checkbox"]');
            const card = toggle.querySelector('.phase-card');
            const deadline = toggle.querySelector('.phase-deadline');
            const deadlineInput = deadline ? deadline.querySelector('input[type="date"]') : null;
            
            // Remove existing event listeners by cloning
            if (card) {
                const newCard = card.cloneNode(true);
                card.parentNode.replaceChild(newCard, card);
                
                newCard.addEventListener('click', (e) => {
                    e.preventDefault();
                    checkbox.checked = !checkbox.checked;
                    updatePhaseToggle(toggle);
                    console.log(`Toggled phase: ${toggle.dataset.phase}`);
                });
            }
            
            if (checkbox) {
                checkbox.addEventListener('change', () => {
                    updatePhaseToggle(toggle);
                    console.log(`Changed phase: ${toggle.dataset.phase}`);
                });
            }
            
            // Initialize state
            updatePhaseToggle(toggle);
        });
        
        console.log(`✅ Reinitialized ${phaseToggles.length} phase toggles`);
        
        function updatePhaseToggle(toggle) {
            const checkbox = toggle.querySelector('input[type="checkbox"]');
            const deadline = toggle.querySelector('.phase-deadline');
            const deadlineInput = deadline ? deadline.querySelector('input[type="date"]') : null;
            
            if (checkbox && checkbox.checked) {
                toggle.classList.add('active');
                if (deadline) deadline.style.display = 'block';
                if (deadlineInput) deadlineInput.required = true;
            } else {
                toggle.classList.remove('active');
                if (deadline) deadline.style.display = 'none';
                if (deadlineInput) {
                    deadlineInput.required = false;
                    deadlineInput.value = '';
                }
            }
        }
    }
    
    // Function to add debug mode
    function enableDebugMode() {
        document.body.classList.add('debug-step2');
        
        // Add debug info
        const debugInfo = document.createElement('div');
        debugInfo.id = 'step2-debug-info';
        debugInfo.style.cssText = `
            position: fixed;
            top: 10px;
            right: 10px;
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 10px;
            border-radius: 5px;
            font-family: monospace;
            font-size: 12px;
            z-index: 9999;
            max-width: 300px;
        `;
        
        function updateDebugInfo() {
            const step2 = document.querySelector('[data-step="2"]');
            const phasesGrid = document.querySelector('.phases-grid');
            const phaseToggles = document.querySelectorAll('.phase-toggle');
            
            debugInfo.innerHTML = `
                <strong>Step 2 Debug Info:</strong><br>
                Step 2 exists: ${!!step2}<br>
                Step 2 active: ${step2?.classList.contains('active')}<br>
                Phases grid exists: ${!!phasesGrid}<br>
                Phase toggles: ${phaseToggles.length}<br>
                Current step: ${document.querySelector('.step-content.active')?.dataset.step || 'none'}<br>
                <button onclick="window.fixStep2Debug()" style="margin-top: 5px; padding: 2px 5px;">Re-fix</button>
            `;
        }
        
        document.body.appendChild(debugInfo);
        updateDebugInfo();
        
        // Update debug info every 2 seconds
        setInterval(updateDebugInfo, 2000);
        
        console.log('✅ Debug mode enabled');
    }
    
    // Main fix function
    function applyFix() {
        fixStep2Visibility();
        forceStep2Visible();
        reinitializePhaseToggles();
        enableDebugMode();
        
        // Make fix function globally available
        window.fixStep2Debug = applyFix;
        
        console.log('🎉 Step 2 visibility fix applied!');
        console.log('If you still don\'t see Step 2 content:');
        console.log('1. Check browser console for errors');
        console.log('2. Try calling window.fixStep2Debug() again');
        console.log('3. Look for the debug info box in top-right corner');
    }
    
    // Apply fix when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', applyFix);
    } else {
        applyFix();
    }
    
    // Also apply fix when Step 2 becomes active
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                const target = mutation.target;
                if (target.dataset.step === '2' && target.classList.contains('active')) {
                    console.log('Step 2 became active, applying fix...');
                    setTimeout(applyFix, 100);
                }
            }
        });
    });
    
    // Start observing
    const step2 = document.querySelector('[data-step="2"]');
    if (step2) {
        observer.observe(step2, { attributes: true, attributeFilter: ['class'] });
    }
    
})();