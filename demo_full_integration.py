#!/usr/bin/env python3
"""
Full Integration Demo: PhaseManager + PhaseTaskGenerator
Shows complete workflow from phase creation to task generation
"""

from app import PhaseManager, PhaseTaskGenerator, PHASE_TEMPLATES
from datetime import date, timedelta

def demo_full_integration():
    """Demonstrate complete phase management and task generation workflow"""
    print("🚀 Complete Multi-Phase Project Management Demo")
    print("=" * 60)
    
    # Student preferences
    work_preferences = {
        'monday': 'light',
        'tuesday': 'heavy',
        'wednesday': 'light', 
        'thursday': 'heavy',
        'friday': 'light'
    }
    
    print("\n👤 Student Profile:")
    print("  Name: Alex Research Student")
    print("  Project: Impact of Social Media on Political Discourse")
    print("  Work Schedule:")
    for day, intensity in work_preferences.items():
        capacity = "2 tasks" if intensity == 'heavy' else "1 task"
        print(f"    {day.capitalize()}: {intensity} ({capacity})")
    
    # Phase selection and deadlines
    selected_phases = ['literature_review', 'research_question', 'methods_planning']
    deadlines = {
        'literature_review': date.today() + timedelta(days=30),
        'research_question': date.today() + timedelta(days=50), 
        'methods_planning': date.today() + timedelta(days=80)
    }
    
    print(f"\n📋 Selected Research Phases:")
    for i, phase_type in enumerate(selected_phases, 1):
        template = PhaseManager.get_phase_template(phase_type)
        deadline = deadlines[phase_type]
        print(f"  {i}. {template['icon']} {template['name']}")
        print(f"     Deadline: {deadline}")
        print(f"     Duration: {template['default_duration_weeks']} weeks")
    
    # Validate deadlines
    print(f"\n✅ Deadline Validation:")
    is_valid = PhaseManager.validate_phase_deadlines(selected_phases, deadlines)
    print(f"  Chronological order check: {'✓ Valid' if is_valid else '✗ Invalid'}")
    
    if not is_valid:
        print("  ⚠️  Deadlines must be in logical order!")
        return
    
    # Simulate phase creation (without database)
    print(f"\n🏗️  Phase Creation Simulation:")
    
    mock_phases = []
    for i, phase_type in enumerate(selected_phases, 1):
        template = PhaseManager.get_phase_template(phase_type)
        
        # Mock phase object
        class MockPhase:
            def __init__(self, phase_type, name, deadline, order):
                self.phase_type = phase_type
                self.phase_name = name
                self.deadline = deadline
                self.order_index = order
                self.id = order
                self.is_active = True
        
        phase = MockPhase(
            phase_type=phase_type,
            name=template['name'],
            deadline=deadlines[phase_type],
            order=i
        )
        mock_phases.append(phase)
        
        print(f"  Created: {template['icon']} {phase.phase_name} (Order: {phase.order_index})")
    
    # Generate tasks for each phase
    print(f"\n⚡ Task Generation for Each Phase:")
    
    total_tasks_generated = 0
    
    for phase in mock_phases:
        print(f"\n  📌 {phase.phase_name}:")
        
        # Get task templates
        templates = PhaseTaskGenerator.get_task_template(phase.phase_type)
        print(f"    Available task templates: {len(templates)}")
        
        # Calculate work capacity until deadline
        slots = PhaseTaskGenerator._calculate_available_slots(work_preferences, phase.deadline)
        total_capacity = sum(slot['capacity'] for slot in slots)
        print(f"    Work capacity until deadline: {total_capacity} tasks over {len(slots)} days")
        
        # Generate tasks (simulate first 8 tasks to avoid too much output)
        sample_templates = templates[:min(8, len(templates))]
        tasks = PhaseTaskGenerator.distribute_tasks_by_intensity(
            sample_templates, work_preferences, phase.deadline, phase.id
        )
        
        print(f"    Generated tasks: {len(tasks)}")
        total_tasks_generated += len(tasks)
        
        # Show task type distribution
        task_types = {}
        for task in tasks:
            task_type = task.task_type
            task_types[task_type] = task_types.get(task_type, 0) + 1
        
        print(f"    Task type distribution:")
        for task_type, count in sorted(task_types.items()):
            print(f"      {task_type}: {count} tasks")
        
        # Show first few tasks
        print(f"    Sample tasks:")
        for i, task in enumerate(tasks[:3], 1):
            day_name = task.date.strftime('%A')
            print(f"      {i}. [{task.task_type}] {task.date} ({day_name})")
            print(f"         {task.task_description[:60]}...")
        
        if len(tasks) > 3:
            print(f"      ... and {len(tasks) - 3} more tasks")
    
    # Summary
    print(f"\n📊 Project Summary:")
    print(f"  Total phases: {len(mock_phases)}")
    print(f"  Total tasks generated: {total_tasks_generated}")
    print(f"  Project duration: {(max(deadlines.values()) - date.today()).days} days")
    
    # Show integrated timeline
    print(f"\n📅 Integrated Project Timeline:")
    sorted_phases = sorted(mock_phases, key=lambda p: p.deadline)
    
    for phase in sorted_phases:
        days_until = (phase.deadline - date.today()).days
        template = PhaseManager.get_phase_template(phase.phase_type)
        print(f"  {template['icon']} {phase.phase_name}: {phase.deadline} ({days_until} days)")
    
    print(f"\n🎉 Multi-Phase Project Management System Demo Complete!")
    print(f"The system successfully:")
    print(f"  ✓ Validated phase deadlines in chronological order")
    print(f"  ✓ Created {len(mock_phases)} research phases with proper ordering")
    print(f"  ✓ Generated {total_tasks_generated} phase-specific tasks")
    print(f"  ✓ Distributed tasks based on work day preferences")
    print(f"  ✓ Classified tasks by type for better organization")
    print(f"  ✓ Created an integrated project timeline")

if __name__ == '__main__':
    demo_full_integration()