#!/usr/bin/env python3
"""
Demonstration of PhaseTaskGenerator
Shows phase-specific task generation and distribution
"""

from app import PhaseTaskGenerator, PHASE_TEMPLATES
from datetime import date, timedelta

def demo_task_generation():
    """Demonstrate the phase-specific task generation system"""
    print("🎯 Phase-Specific Task Generation Demo")
    print("=" * 50)
    
    # Sample work preferences
    work_preferences = {
        'monday': 'light',
        'tuesday': 'heavy', 
        'wednesday': 'light',
        'thursday': 'heavy',
        'friday': 'light'
    }
    
    print("\n📅 Work Preferences:")
    for day, intensity in work_preferences.items():
        capacity = "2 tasks" if intensity == 'heavy' else "1 task"
        print(f"  {day.capitalize()}: {intensity} ({capacity})")
    
    # Demo task type determination
    print("\n🔍 Task Type Classification Examples:")
    sample_tasks = [
        "Read 3 academic articles on topic",
        "Draft literature review outline", 
        "Meet with adviser to discuss progress",
        "Identify research gaps from literature",
        "Complete IRB application",
        "Analyze thematic patterns in sources",
        "Design survey instrument",
        "Update progress tracking"
    ]
    
    for task in sample_tasks:
        task_type = PhaseTaskGenerator._determine_task_type(task)
        print(f"  '{task}' → {task_type}")
    
    # Demo available slots calculation
    deadline = date.today() + timedelta(days=14)  # 2 weeks from now
    print(f"\n📊 Available Work Slots (until {deadline}):")
    
    slots = PhaseTaskGenerator._calculate_available_slots(work_preferences, deadline)
    
    total_capacity = 0
    for slot in slots[:7]:  # Show first week
        day_name = slot['date'].strftime('%A')
        print(f"  {slot['date']} ({day_name}): {slot['intensity']} - {slot['capacity']} task(s)")
        total_capacity += slot['capacity']
    
    if len(slots) > 7:
        print(f"  ... and {len(slots) - 7} more work days")
        total_capacity += sum(slot['capacity'] for slot in slots[7:])
    
    print(f"  Total capacity: {total_capacity} tasks over {len(slots)} work days")
    
    # Demo task generation for different phases
    print("\n📚 Task Generation by Phase:")
    
    phases_to_demo = ['literature_review', 'research_question', 'methods_planning']
    
    for phase_type in phases_to_demo:
        print(f"\n  {PHASE_TEMPLATES[phase_type]['icon']} {PHASE_TEMPLATES[phase_type]['name']}:")
        
        # Get task templates for this phase
        templates = PhaseTaskGenerator.get_task_template(phase_type)
        print(f"    Available templates: {len(templates)}")
        
        # Show sample tasks with their types
        for i, template in enumerate(templates[:3], 1):
            task_type = PhaseTaskGenerator._determine_task_type(template)
            print(f"    {i}. [{task_type}] {template}")
        
        if len(templates) > 3:
            print(f"    ... and {len(templates) - 3} more tasks")
    
    # Demo task distribution simulation
    print("\n⚡ Task Distribution Simulation:")
    print("  (Simulating Literature Review phase)")
    
    # Mock phase object for demonstration
    class MockPhase:
        def __init__(self):
            self.phase_type = 'literature_review'
            self.deadline = date.today() + timedelta(days=14)
            self.id = 1
    
    mock_phase = MockPhase()
    
    # Get first 10 tasks for demo
    lit_templates = PhaseTaskGenerator.get_task_template('literature_review')[:10]
    
    # Simulate task distribution
    distributed_tasks = PhaseTaskGenerator.distribute_tasks_by_intensity(
        lit_templates, work_preferences, mock_phase.deadline, mock_phase.id
    )
    
    print(f"  Generated {len(distributed_tasks)} tasks from {len(lit_templates)} templates")
    
    # Group tasks by date for display
    tasks_by_date = {}
    for task in distributed_tasks:
        date_key = task.date
        if date_key not in tasks_by_date:
            tasks_by_date[date_key] = []
        tasks_by_date[date_key].append(task)
    
    # Show first few days
    sorted_dates = sorted(tasks_by_date.keys())
    for i, task_date in enumerate(sorted_dates[:5]):
        day_name = task_date.strftime('%A')
        day_tasks = tasks_by_date[task_date]
        
        print(f"  {task_date} ({day_name}) - {len(day_tasks)} task(s):")
        for task in day_tasks:
            print(f"    • [{task.task_type}] {task.task_description[:50]}...")
    
    if len(sorted_dates) > 5:
        remaining_tasks = sum(len(tasks_by_date[d]) for d in sorted_dates[5:])
        print(f"  ... and {remaining_tasks} more tasks on {len(sorted_dates) - 5} additional days")
    
    print("\n🎉 Phase-Specific Task Generation is working correctly!")
    print("Tasks are distributed based on work preferences and phase requirements.")

if __name__ == '__main__':
    demo_task_generation()