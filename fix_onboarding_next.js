// Fixed Onboarding JavaScript - removes duplicate methods
class OnboardingWizard {
    constructor() {
        this.currentStep = 1;
        this.totalSteps = 4;
        this.formData = {};
        
        this.init();
        this.loadFromStorage();
    }
    
    init() {
        this.bindEvents();
        this.updateProgress();
        this.initPhaseToggles();
        this.initPresets();
        this.initAutoSave();
    }
    
    bindEvents() {
        // Navigation
        document.getElementById('next-btn').addEventListener('click', () => this.nextStep());
        document.getElementById('prev-btn').addEventListener('click', () => this.prevStep());
        document.getElementById('submit-btn').addEventListener('click', (e) => this.handleSubmit(e));
        
        // Auto-suggest deadlines
        const autoSuggestBtn = document.getElementById('auto-suggest-deadlines');
        if (autoSuggestBtn) {
            autoSuggestBtn.addEventListener('click', () => this.autoSuggestDeadlines());
        }
        
        // Form inputs
        const projectTitle = document.getElementById('project_title');
        const thesisDeadline = document.getElementById('thesis_deadline');
        
        if (projectTitle) projectTitle.addEventListener('input', () => this.saveToStorage());
        if (thesisDeadline) thesisDeadline.addEventListener('change', () => this.saveToStorage());
        
        // Keyboard navigation
        document.addEventListener('keydown', (e) => this.handleKeyboard(e));
    }
    
    initPhaseToggles() {
        const phaseToggles = document.querySelectorAll('.phase-toggle');
        
        phaseToggles.forEach(toggle => {
            const checkbox = toggle.querySelector('input[type="checkbox"]');
            const card = toggle.querySelector('.phase-card');
            
            if (card) {
                card.addEventListener('click', (e) => {
                    e.preventDefault();
                    checkbox.checked = !checkbox.checked;
                    this.updatePhaseToggle(toggle);
                    this.saveToStorage();
                });
            }
            
            if (checkbox) {
                checkbox.addEventListener('change', () => {
                    this.updatePhaseToggle(toggle);
                    this.saveToStorage();
                });
            }
            
            // Initialize state
            this.updatePhaseToggle(toggle);
        });
    }
    
    updatePhaseToggle(toggle) {
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
    
    initPresets() {
        const presetCards = document.querySelectorAll('.preset-card');
        
        presetCards.forEach(card => {
            card.addEventListener('click', () => {
                // Remove active from all cards
                presetCards.forEach(c => c.classList.remove('active'));
                card.classList.add('active');
                
                const preset = card.dataset.preset;
                this.applyPreset(preset);
                this.saveToStorage();
            });
        });
    }
    
    applyPreset(preset) {
        const presets = {
            balanced: {
                monday: 'light', tuesday: 'light', wednesday: 'light', 
                thursday: 'light', friday: 'light', saturday: 'none', sunday: 'none'
            },
            intensive: {
                monday: 'heavy', tuesday: 'none', wednesday: 'heavy', 
                thursday: 'none', friday: 'heavy', saturday: 'none', sunday: 'none'
            },
            weekend: {
                monday: 'none', tuesday: 'none', wednesday: 'none', 
                thursday: 'none', friday: 'light', saturday: 'heavy', sunday: 'heavy'
            }
        };
        
        const schedule = presets[preset];
        if (!schedule) return;
        
        Object.entries(schedule).forEach(([day, intensity]) => {
            const radio = document.querySelector(`input[name="${day}_intensity"][value="${intensity}"]`);
            if (radio) radio.checked = true;
        });
    }
    
    nextStep() {
        console.log('nextStep called, current step:', this.currentStep);
        
        if (!this.validateCurrentStep()) {
            console.log('Validation failed');
            return;
        }
        
        if (this.currentStep < this.totalSteps) {
            this.currentStep++;
            console.log('Moving to step:', this.currentStep);
            this.updateStep();
            this.updateProgress();
            this.saveToStorage();
        }
    }
    
    prevStep() {
        console.log('prevStep called, current step:', this.currentStep);
        
        if (this.currentStep > 1) {
            this.currentStep--;
            console.log('Moving back to step:', this.currentStep);
            this.updateStep();
            this.updateProgress();
            this.saveToStorage();
        }
    }
    
    updateStep() {
        console.log('updateStep called for step:', this.currentStep);
        
        // Hide all step content
        document.querySelectorAll('.step-content').forEach(step => {
            step.classList.remove('active');
        });
        
        // Show current step
        const currentStepContent = document.querySelector(`[data-step="${this.currentStep}"]`);
        if (currentStepContent) {
            currentStepContent.classList.add('active');
            console.log('Activated step content for step:', this.currentStep);
        } else {
            console.error('Could not find step content for step:', this.currentStep);
        }
        
        // Update step indicators
        document.querySelectorAll('.progress-steps .step').forEach((step, index) => {
            if (index + 1 <= this.currentStep) {
                step.classList.add('active');
            } else {
                step.classList.remove('active');
            }
        });
        
        // Update navigation buttons
        const prevBtn = document.getElementById('prev-btn');
        const nextBtn = document.getElementById('next-btn');
        const submitBtn = document.getElementById('submit-btn');
        
        if (prevBtn) prevBtn.style.display = this.currentStep > 1 ? 'flex' : 'none';
        
        if (this.currentStep === this.totalSteps) {
            if (nextBtn) nextBtn.style.display = 'none';
            if (submitBtn) submitBtn.style.display = 'flex';
            this.updateReview();
        } else {
            if (nextBtn) nextBtn.style.display = 'flex';
            if (submitBtn) submitBtn.style.display = 'none';
        }
    }
    
    updateProgress() {
        const progressFill = document.getElementById('progress-fill');
        if (progressFill) {
            const percentage = (this.currentStep / this.totalSteps) * 100;
            progressFill.style.width = `${percentage}%`;
        }
    }
    
    validateCurrentStep() {
        console.log('Validating step:', this.currentStep);
        
        const currentStepContent = document.querySelector(`[data-step="${this.currentStep}"]`);
        if (!currentStepContent) {
            console.error('No step content found for step:', this.currentStep);
            return false;
        }
        
        const requiredInputs = currentStepContent.querySelectorAll('input[required]');
        let isValid = true;
        
        requiredInputs.forEach(input => {
            if (!input.value.trim()) {
                input.style.borderColor = '#ef4444';
                isValid = false;
                console.log('Required field empty:', input.name || input.id);
            } else {
                input.style.borderColor = '#e5e7eb';
            }
        });
        
        // Special validation for step 2 (phases)
        if (this.currentStep === 2) {
            const selectedPhases = document.querySelectorAll('input[name="selected_phases"]:checked');
            if (selectedPhases.length === 0) {
                alert('Please select at least one research phase.');
                return false;
            }
            
            // Validate deadlines for selected phases
            let deadlineValid = true;
            selectedPhases.forEach(phase => {
                const phaseValue = phase.value;
                const deadlineInput = document.querySelector(`input[name="${phaseValue}_deadline"]`);
                if (deadlineInput && !deadlineInput.value) {
                    deadlineInput.style.borderColor = '#ef4444';
                    deadlineValid = false;
                } else if (deadlineInput) {
                    deadlineInput.style.borderColor = '#e5e7eb';
                }
            });
            
            if (!deadlineValid) {
                alert('Please set deadlines for all selected phases.');
                return false;
            }
        }
        
        console.log('Validation result:', isValid);
        return isValid;
    }
    
    autoSuggestDeadlines() {
        const thesisDeadline = document.getElementById('thesis_deadline').value;
        if (!thesisDeadline) {
            alert('Please set your thesis deadline first.');
            return;
        }
        
        const thesisDate = new Date(thesisDeadline);
        const selectedPhases = document.querySelectorAll('input[name="selected_phases"]:checked');
        
        if (selectedPhases.length === 0) {
            alert('Please select your research phases first.');
            return;
        }
        
        // Calculate suggested deadlines working backwards from thesis deadline
        const phaseDurations = {
            'literature_review': 30, // 30 days
            'research_question': 14, // 14 days  
            'methods_planning': 21, // 21 days
            'irb_proposal': 14 // 14 days
        };
        
        let currentDate = new Date(thesisDate);
        const phases = Array.from(selectedPhases).reverse(); // Work backwards
        
        phases.forEach(phase => {
            const phaseValue = phase.value;
            const duration = phaseDurations[phaseValue] || 14;
            
            currentDate.setDate(currentDate.getDate() - duration);
            
            const deadlineInput = document.querySelector(`input[name="${phaseValue}_deadline"]`);
            if (deadlineInput) {
                deadlineInput.value = currentDate.toISOString().split('T')[0];
            }
        });
        
        this.saveToStorage();
    }
    
    updateReview() {
        // Update project info
        const titleEl = document.getElementById('review-title');
        const deadlineEl = document.getElementById('review-deadline');
        
        if (titleEl) {
            const title = document.getElementById('project_title');
            titleEl.textContent = title ? title.value : '-';
        }
        
        if (deadlineEl) {
            const deadline = document.getElementById('thesis_deadline');
            deadlineEl.textContent = deadline ? deadline.value : '-';
        }
        
        // Update phases
        const selectedPhases = document.querySelectorAll('input[name="selected_phases"]:checked');
        const reviewPhases = document.getElementById('review-phases');
        
        if (reviewPhases) {
            reviewPhases.innerHTML = '';
            
            selectedPhases.forEach(phase => {
                const phaseValue = phase.value;
                const phaseName = this.getPhaseDisplayName(phaseValue);
                const deadlineInput = document.querySelector(`input[name="${phaseValue}_deadline"]`);
                const deadline = deadlineInput ? deadlineInput.value : '-';
                
                const phaseItem = document.createElement('div');
                phaseItem.className = 'review-item';
                phaseItem.innerHTML = `
                    <span class="review-label">${phaseName}:</span>
                    <span class="review-value">${deadline}</span>
                `;
                reviewPhases.appendChild(phaseItem);
            });
        }
        
        // Update schedule
        const reviewSchedule = document.getElementById('review-schedule');
        if (reviewSchedule) {
            reviewSchedule.innerHTML = '';
            
            const days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];
            const dayNames = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
            
            days.forEach((day, index) => {
                const selectedIntensity = document.querySelector(`input[name="${day}_intensity"]:checked`);
                const intensity = selectedIntensity ? selectedIntensity.value : 'none';
                
                if (intensity !== 'none') {
                    const scheduleItem = document.createElement('div');
                    scheduleItem.className = 'review-item';
                    scheduleItem.innerHTML = `
                        <span class="review-label">${dayNames[index]}:</span>
                        <span class="review-value">${intensity.charAt(0).toUpperCase() + intensity.slice(1)}</span>
                    `;
                    reviewSchedule.appendChild(scheduleItem);
                }
            });
        }
    }
    
    getPhaseDisplayName(phaseType) {
        const names = {
            'literature_review': 'Literature Review',
            'research_question': 'Research Question Development',
            'methods_planning': 'Methods Planning',
            'irb_proposal': 'IRB Proposal'
        };
        return names[phaseType] || phaseType;
    }
    
    handleSubmit(e) {
        if (!this.validateCurrentStep()) {
            e.preventDefault();
            return false;
        }
        
        // Clear localStorage on successful submission
        localStorage.removeItem('paperpacer_onboarding');
        return true;
    }
    
    handleKeyboard(e) {
        if (e.key === 'Enter' && e.ctrlKey) {
            if (this.currentStep < this.totalSteps) {
                this.nextStep();
            } else {
                const submitBtn = document.getElementById('submit-btn');
                if (submitBtn) submitBtn.click();
            }
        } else if (e.key === 'Escape') {
            if (this.currentStep > 1) {
                this.prevStep();
            }
        }
    }
    
    // Auto-save functionality
    initAutoSave() {
        setInterval(() => this.saveToStorage(), 5000); // Save every 5 seconds
    }
    
    saveToStorage() {
        const form = document.getElementById('onboarding-form');
        if (!form) return;
        
        const formData = new FormData(form);
        const data = {};
        
        for (let [key, value] of formData.entries()) {
            if (data[key]) {
                if (Array.isArray(data[key])) {
                    data[key].push(value);
                } else {
                    data[key] = [data[key], value];
                }
            } else {
                data[key] = value;
            }
        }
        
        data.currentStep = this.currentStep;
        localStorage.setItem('paperpacer_onboarding', JSON.stringify(data));
    }
    
    loadFromStorage() {
        const saved = localStorage.getItem('paperpacer_onboarding');
        if (!saved) return;
        
        try {
            const data = JSON.parse(saved);
            
            // Restore form values
            Object.entries(data).forEach(([key, value]) => {
                if (key === 'currentStep') {
                    this.currentStep = value;
                    return;
                }
                
                const input = document.querySelector(`[name="${key}"]`);
                if (input) {
                    if (input.type === 'checkbox' || input.type === 'radio') {
                        if (Array.isArray(value)) {
                            value.forEach(v => {
                                const specificInput = document.querySelector(`[name="${key}"][value="${v}"]`);
                                if (specificInput) specificInput.checked = true;
                            });
                        } else {
                            const specificInput = document.querySelector(`[name="${key}"][value="${value}"]`);
                            if (specificInput) specificInput.checked = true;
                        }
                    } else {
                        input.value = value;
                    }
                }
            });
            
            // Update UI
            this.updateStep();
            this.updateProgress();
            this.initPhaseToggles();
            
        } catch (e) {
            console.error('Failed to load saved data:', e);
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing OnboardingWizard');
    new OnboardingWizard();
});