#!/usr/bin/env python3
"""
Simple test to verify onboarding Next button functionality
"""

from flask import Flask, render_template_string

app = Flask(__name__)

# Minimal onboarding template with working JavaScript
ONBOARDING_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Test Onboarding</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .step-content { display: none; padding: 20px; border: 1px solid #ccc; margin: 10px 0; }
        .step-content.active { display: block; background: #f9f9f9; }
        .btn-primary { background: #3b82f6; color: white; padding: 12px 24px; border: none; border-radius: 5px; cursor: pointer; margin: 5px; }
        .btn-secondary { background: #6b7280; color: white; padding: 12px 24px; border: none; border-radius: 5px; cursor: pointer; margin: 5px; }
        input { padding: 8px; border: 1px solid #ccc; border-radius: 4px; width: 200px; margin: 5px 0; }
        label { display: block; margin: 5px 0; font-weight: 500; }
        .form-group { margin-bottom: 15px; }
        .progress-bar { width: 100%; height: 8px; background: #e5e7eb; border-radius: 4px; overflow: hidden; margin-bottom: 20px; }
        .progress-fill { height: 100%; background: #3b82f6; transition: width 0.3s ease; width: 25%; }
    </style>
</head>
<body>
    <h1>Onboarding Test - Next Button Fix</h1>
    
    <div class="progress-bar">
        <div class="progress-fill" id="progress-fill"></div>
    </div>
    
    <p>Current Step: <span id="current-step">1</span> of 4</p>

    <form id="onboarding-form">
        <!-- Step 1 -->
        <div class="step-content active" data-step="1">
            <h2>Step 1: Project Information</h2>
            <div class="form-group">
                <label for="project_title">Project Title</label>
                <input type="text" id="project_title" name="project_title" required placeholder="Enter your project title">
            </div>
            <div class="form-group">
                <label for="thesis_deadline">Thesis Deadline</label>
                <input type="date" id="thesis_deadline" name="thesis_deadline" required>
            </div>
        </div>

        <!-- Step 2 -->
        <div class="step-content" data-step="2">
            <h2>Step 2: Research Phases</h2>
            <div class="form-group">
                <label><input type="checkbox" name="selected_phases" value="literature_review" checked> Literature Review</label>
                <label><input type="checkbox" name="selected_phases" value="methods_planning"> Methods Planning</label>
            </div>
        </div>

        <!-- Step 3 -->
        <div class="step-content" data-step="3">
            <h2>Step 3: Work Schedule</h2>
            <div class="form-group">
                <label>Work Intensity:</label>
                <label><input type="radio" name="work_intensity" value="light" checked> Light</label>
                <label><input type="radio" name="work_intensity" value="heavy"> Heavy</label>
            </div>
        </div>

        <!-- Step 4 -->
        <div class="step-content" data-step="4">
            <h2>Step 4: Review & Submit</h2>
            <p>Review your selections and submit your project setup.</p>
            <div id="review-content">
                <!-- Will be populated by JavaScript -->
            </div>
        </div>

        <!-- Navigation -->
        <div class="step-navigation">
            <button type="button" class="btn-secondary" id="prev-btn" style="display: none;">← Previous</button>
            <button type="button" class="btn-primary" id="next-btn">Next →</button>
            <button type="submit" class="btn-primary" id="submit-btn" style="display: none;">✓ Submit</button>
        </div>
    </form>

    <div id="debug" style="margin-top: 20px; padding: 10px; background: #f0f0f0; border-radius: 5px;">
        <h3>Debug Log:</h3>
        <div id="debug-log" style="font-family: monospace; font-size: 12px; max-height: 150px; overflow-y: auto;"></div>
    </div>

    <script>
        // Simple, clean onboarding JavaScript
        class SimpleOnboarding {
            constructor() {
                this.currentStep = 1;
                this.totalSteps = 4;
                this.init();
            }
            
            init() {
                this.log('Initializing onboarding wizard');
                this.bindEvents();
                this.updateDisplay();
            }
            
            bindEvents() {
                const nextBtn = document.getElementById('next-btn');
                const prevBtn = document.getElementById('prev-btn');
                const submitBtn = document.getElementById('submit-btn');
                
                if (nextBtn) {
                    nextBtn.addEventListener('click', () => this.nextStep());
                    this.log('Next button event bound');
                }
                
                if (prevBtn) {
                    prevBtn.addEventListener('click', () => this.prevStep());
                    this.log('Previous button event bound');
                }
                
                if (submitBtn) {
                    submitBtn.addEventListener('click', (e) => this.handleSubmit(e));
                    this.log('Submit button event bound');
                }
            }
            
            nextStep() {
                this.log(`Next button clicked - current step: ${this.currentStep}`);
                
                if (!this.validateCurrentStep()) {
                    this.log('Validation failed, staying on current step');
                    return;
                }
                
                if (this.currentStep < this.totalSteps) {
                    this.currentStep++;
                    this.log(`Moving to step ${this.currentStep}`);
                    this.updateDisplay();
                } else {
                    this.log('Already on last step');
                }
            }
            
            prevStep() {
                this.log(`Previous button clicked - current step: ${this.currentStep}`);
                
                if (this.currentStep > 1) {
                    this.currentStep--;
                    this.log(`Moving back to step ${this.currentStep}`);
                    this.updateDisplay();
                } else {
                    this.log('Already on first step');
                }
            }
            
            validateCurrentStep() {
                this.log(`Validating step ${this.currentStep}`);
                
                const currentStepContent = document.querySelector(`[data-step="${this.currentStep}"]`);
                if (!currentStepContent) {
                    this.log('ERROR: No step content found');
                    return false;
                }
                
                const requiredInputs = currentStepContent.querySelectorAll('input[required]');
                let isValid = true;
                
                requiredInputs.forEach(input => {
                    if (!input.value.trim()) {
                        input.style.borderColor = '#ef4444';
                        isValid = false;
                        this.log(`Required field empty: ${input.name || input.id}`);
                    } else {
                        input.style.borderColor = '#ccc';
                    }
                });
                
                // Step 2 validation - at least one phase selected
                if (this.currentStep === 2) {
                    const selectedPhases = document.querySelectorAll('input[name="selected_phases"]:checked');
                    if (selectedPhases.length === 0) {
                        alert('Please select at least one research phase.');
                        isValid = false;
                    }
                }
                
                this.log(`Validation result: ${isValid}`);
                return isValid;
            }
            
            updateDisplay() {
                this.log(`Updating display for step ${this.currentStep}`);
                
                // Hide all steps
                document.querySelectorAll('.step-content').forEach(step => {
                    step.classList.remove('active');
                });
                
                // Show current step
                const currentStepContent = document.querySelector(`[data-step="${this.currentStep}"]`);
                if (currentStepContent) {
                    currentStepContent.classList.add('active');
                    this.log(`Activated step ${this.currentStep}`);
                } else {
                    this.log(`ERROR: Could not find step ${this.currentStep}`);
                }
                
                // Update progress bar
                const progressFill = document.getElementById('progress-fill');
                if (progressFill) {
                    const percentage = (this.currentStep / this.totalSteps) * 100;
                    progressFill.style.width = `${percentage}%`;
                }
                
                // Update step counter
                const stepCounter = document.getElementById('current-step');
                if (stepCounter) {
                    stepCounter.textContent = this.currentStep;
                }
                
                // Update navigation buttons
                const prevBtn = document.getElementById('prev-btn');
                const nextBtn = document.getElementById('next-btn');
                const submitBtn = document.getElementById('submit-btn');
                
                if (prevBtn) prevBtn.style.display = this.currentStep > 1 ? 'inline-block' : 'none';
                
                if (this.currentStep === this.totalSteps) {
                    if (nextBtn) nextBtn.style.display = 'none';
                    if (submitBtn) submitBtn.style.display = 'inline-block';
                    this.updateReview();
                } else {
                    if (nextBtn) nextBtn.style.display = 'inline-block';
                    if (submitBtn) submitBtn.style.display = 'none';
                }
            }
            
            updateReview() {
                this.log('Updating review content');
                
                const reviewContent = document.getElementById('review-content');
                if (!reviewContent) return;
                
                const title = document.getElementById('project_title').value || 'Not specified';
                const deadline = document.getElementById('thesis_deadline').value || 'Not specified';
                const selectedPhases = Array.from(document.querySelectorAll('input[name="selected_phases"]:checked'))
                    .map(cb => cb.value).join(', ') || 'None selected';
                const workIntensity = document.querySelector('input[name="work_intensity"]:checked')?.value || 'Not specified';
                
                reviewContent.innerHTML = `
                    <div><strong>Project Title:</strong> ${title}</div>
                    <div><strong>Thesis Deadline:</strong> ${deadline}</div>
                    <div><strong>Selected Phases:</strong> ${selectedPhases}</div>
                    <div><strong>Work Intensity:</strong> ${workIntensity}</div>
                `;
            }
            
            handleSubmit(e) {
                e.preventDefault();
                this.log('Form submitted');
                alert('Form would be submitted now! (This is just a test)');
                return false;
            }
            
            log(message) {
                const debugLog = document.getElementById('debug-log');
                if (debugLog) {
                    const logEntry = document.createElement('div');
                    logEntry.textContent = `${new Date().toLocaleTimeString()}: ${message}`;
                    debugLog.appendChild(logEntry);
                    debugLog.scrollTop = debugLog.scrollHeight;
                }
                console.log(message);
            }
        }
        
        // Initialize when DOM is ready
        document.addEventListener('DOMContentLoaded', () => {
            new SimpleOnboarding();
        });
    </script>
</body>
</html>
'''

@app.route('/')
def test_onboarding():
    return render_template_string(ONBOARDING_TEMPLATE)

if __name__ == '__main__':
    print("Starting test server...")
    print("Open http://localhost:5000 to test the onboarding Next button")
    app.run(debug=True, port=5000)