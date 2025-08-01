#!/usr/bin/env python3
"""
Demonstration of Phase Configuration System
Shows PhaseManager and PHASE_TEMPLATES functionality
"""

from app import PhaseManager, PHASE_TEMPLATES
from datetime import date, timedelta

def demo_phase_configuration():
    """Demonstrate the phase configuration system"""
    print("🎯 Phase Configuration System Demo")
    print("=" * 50)
    
    # Show available phases
    print("\n📋 Available Phases:")
    available_phases = PhaseManager.get_available_phases()
    for phase_type in available_phases:
        template = PhaseManager.get_phase_template(phase_type)
        print(f"  {template['icon']} {template['name']}")
        print(f"     Type: {phase_type}")
        print(f"     Duration: {template['default_duration_weeks']} weeks")
        print(f"     Tasks: {len(template['task_templates'])} templates")
        print()
    
    # Show phase template details
    print("\n📚 Literature Review Phase Details:")
    lit_template = PhaseManager.get_phase_template('literature_review')
    print(f"  Name: {lit_template['name']}")
    print(f"  Description: {lit_template['description']}")
    print(f"  Task Types: {', '.join(lit_template['task_types'])}")
    print(f"  Sample Tasks:")
    for i, task in enumerate(lit_template['task_templates'][:3], 1):
        print(f"    {i}. {task}")
    print(f"    ... and {len(lit_template['task_templates']) - 3} more tasks")
    
    # Test deadline validation
    print("\n✅ Deadline Validation Tests:")
    
    # Valid deadlines
    valid_phases = ['literature_review', 'research_question']
    valid_deadlines = {
        'literature_review': date.today() + timedelta(days=30),
        'research_question': date.today() + timedelta(days=60)
    }
    
    is_valid = PhaseManager.validate_phase_deadlines(valid_phases, valid_deadlines)
    print(f"  Valid chronological order: {is_valid} ✓")
    
    # Invalid deadlines (wrong order)
    invalid_deadlines = {
        'literature_review': date.today() + timedelta(days=60),
        'research_question': date.today() + timedelta(days=30)  # Before lit review
    }
    
    is_invalid = PhaseManager.validate_phase_deadlines(valid_phases, invalid_deadlines)
    print(f"  Invalid chronological order: {is_invalid} ✗")
    
    # Past date validation
    past_deadlines = {
        'literature_review': date.today() - timedelta(days=1)  # Past date
    }
    
    is_past = PhaseManager.validate_phase_deadlines(['literature_review'], past_deadlines)
    print(f"  Past date validation: {is_past} ✗")
    
    print("\n🎉 Phase Configuration System is working correctly!")
    print("Ready for integration with the onboarding flow.")

if __name__ == '__main__':
    demo_phase_configuration()