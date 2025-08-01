#!/usr/bin/env python3

"""
Demo script for the Schedule Coordinator and Timeline functionality.

This script demonstrates the integrated timeline and schedule coordination features
for multi-phase project management.
"""

import sys
import os
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import the app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, Student, ProjectPhase, PhaseTask, PhaseType
from schedule_coordinator import ScheduleCoordinator, create_timeline_visualization_data
from werkzeug.security import generate_password_hash

def create_demo_data():
    """Create demo data for timeline demonstration"""
    print("🔧 Creating demo data...")
    
    # Create a demo student
    demo_student = Student(
        name="Demo Student",
        email="demo@timeline.com",
        password_hash=generate_password_hash("demo123"),
        project_title="Advanced Machine Learning Applications in Healthcare",
        thesis_deadline=datetime.now().date() + timedelta(days=120),
        lit_review_deadline=datetime.now().date() + timedelta(days=60),
        onboarded=True,
        is_multi_phase=True
    )
    db.session.add(demo_student)
    db.session.commit()
    
    today = datetime.now().date()
    
    # Create phases with realistic deadlines
    phases = [
        ProjectPhase(
            student_id=demo_student.id,
            phase_type=PhaseType.LITERATURE_REVIEW.value,
            phase_name="Literature Review",
            deadline=today + timedelta(days=30),
            order_index=1,
            is_active=True
        ),
        ProjectPhase(
            student_id=demo_student.id,
            phase_type=PhaseType.RESEARCH_QUESTION.value,
            phase_name="Research Question Development",
            deadline=today + timedelta(days=50),
            order_index=2,
            is_active=True
        ),
        ProjectPhase(
            student_id=demo_student.id,
            phase_type=PhaseType.METHODS_PLANNING.value,
            phase_name="Methods Planning",
            deadline=today + timedelta(days=80),
            order_index=3,
            is_active=True
        ),
        ProjectPhase(
            student_id=demo_student.id,
            phase_type=PhaseType.IRB_PROPOSAL.value,
            phase_name="IRB Proposal",
            deadline=today + timedelta(days=100),
            order_index=4,
            is_active=True
        )
    ]
    
    db.session.add_all(phases)
    db.session.commit()
    
    # Create tasks with varying completion status
    tasks = []
    
    # Literature Review tasks (some completed)
    lit_review_tasks = [
        (today + timedelta(days=2), "Search academic databases", "research", "light", True),
        (today + timedelta(days=4), "Read foundational papers", "reading", "heavy", True),
        (today + timedelta(days=6), "Analyze current trends", "analysis", "light", True),
        (today + timedelta(days=8), "Identify research gaps", "analysis", "heavy", False),
        (today + timedelta(days=10), "Synthesize findings", "writing", "heavy", False),
        (today + timedelta(days=12), "Create literature map", "analysis", "light", False),
    ]
    
    for date, desc, task_type, intensity, completed in lit_review_tasks:
        tasks.append(PhaseTask(
            phase_id=phases[0].id,
            date=date,
            task_description=desc,
            task_type=task_type,
            day_intensity=intensity,
            completed=completed
        ))
    
    # Research Question tasks (mostly incomplete)
    research_q_tasks = [
        (today + timedelta(days=35), "Brainstorm research questions", "brainstorming", "light", False),
        (today + timedelta(days=37), "Evaluate feasibility", "analysis", "heavy", False),
        (today + timedelta(days=40), "Refine research focus", "writing", "light", False),
        (today + timedelta(days=42), "Validate with advisor", "meeting", "light", False),
    ]
    
    for date, desc, task_type, intensity, completed in research_q_tasks:
        tasks.append(PhaseTask(
            phase_id=phases[1].id,
            date=date,
            task_description=desc,
            task_type=task_type,
            day_intensity=intensity,
            completed=completed
        ))
    
    # Methods Planning tasks (all incomplete)
    methods_tasks = [
        (today + timedelta(days=55), "Research methodologies", "research", "heavy", False),
        (today + timedelta(days=60), "Design study protocol", "planning", "heavy", False),
        (today + timedelta(days=65), "Plan data collection", "planning", "light", False),
        (today + timedelta(days=70), "Identify tools and resources", "research", "light", False),
    ]
    
    for date, desc, task_type, intensity, completed in methods_tasks:
        tasks.append(PhaseTask(
            phase_id=phases[2].id,
            date=date,
            task_description=desc,
            task_type=task_type,
            day_intensity=intensity,
            completed=completed
        ))
    
    # IRB Proposal tasks (all incomplete)
    irb_tasks = [
        (today + timedelta(days=85), "Draft IRB application", "writing", "heavy", False),
        (today + timedelta(days=90), "Prepare consent forms", "writing", "light", False),
        (today + timedelta(days=95), "Submit IRB proposal", "administrative", "light", False),
    ]
    
    for date, desc, task_type, intensity, completed in irb_tasks:
        tasks.append(PhaseTask(
            phase_id=phases[3].id,
            date=date,
            task_description=desc,
            task_type=task_type,
            day_intensity=intensity,
            completed=completed
        ))
    
    db.session.add_all(tasks)
    db.session.commit()
    
    print(f"✅ Created demo student: {demo_student.name}")
    print(f"✅ Created {len(phases)} phases")
    print(f"✅ Created {len(tasks)} tasks")
    
    return demo_student

def demonstrate_schedule_coordinator(student_id):
    """Demonstrate ScheduleCoordinator functionality"""
    print("\n" + "="*60)
    print("📊 SCHEDULE COORDINATOR DEMONSTRATION")
    print("="*60)
    
    coordinator = ScheduleCoordinator(student_id)
    
    # 1. Show integrated timeline
    print("\n1️⃣ INTEGRATED TIMELINE")
    print("-" * 30)
    timeline = coordinator.get_integrated_timeline()
    
    for event in timeline[:10]:  # Show first 10 events
        print(f"📅 {event.date} | {event.event_type.upper()} | {event.phase_name}")
        print(f"   {event.description} | Criticality: {event.criticality.value}")
        if event.buffer_days > 0:
            print(f"   Buffer: {event.buffer_days} days")
        print()
    
    # 2. Show phase metrics
    print("\n2️⃣ PHASE METRICS")
    print("-" * 30)
    metrics = coordinator.get_phase_metrics()
    
    for metric in metrics:
        print(f"📋 {metric.phase_name}")
        print(f"   Progress: {metric.progress_percentage:.1f}% ({metric.completed_tasks}/{metric.total_tasks} tasks)")
        print(f"   Deadline: {metric.deadline} ({metric.days_remaining} days remaining)")
        print(f"   Criticality: {metric.criticality.value.upper()}")
        print(f"   On Track: {'✅ Yes' if metric.is_on_track else '❌ No'}")
        print(f"   Buffer Days: {metric.buffer_days}")
        if metric.tasks_per_day_required > 0:
            print(f"   Required Tasks/Day: {metric.tasks_per_day_required:.1f}")
        print()
    
    # 3. Show critical path
    print("\n3️⃣ CRITICAL PATH ANALYSIS")
    print("-" * 30)
    critical_path = coordinator.get_critical_path()
    
    for i, item in enumerate(critical_path):
        status = "🔥 CRITICAL" if item['is_critical'] else "✅ Normal"
        print(f"{i+1}. {item['phase_name']} - {status}")
        print(f"   Duration: {item['duration_days']} days | Buffer: {item['buffer_days']} days")
        print(f"   Progress: {item['progress_percentage']:.1f}% | Tasks Remaining: {item['tasks_remaining']}")
        if item['is_critical']:
            print(f"   ⚠️  Reason: {item['criticality_reason']}")
        if item['dependencies']:
            deps = [dep['phase_name'] for dep in item['dependencies']]
            print(f"   Depends on: {', '.join(deps)}")
        print()
    
    return coordinator

def demonstrate_task_redistribution(coordinator):
    """Demonstrate automatic task redistribution"""
    print("\n4️⃣ TASK REDISTRIBUTION DEMO")
    print("-" * 30)
    
    # Get the first phase
    phase = coordinator.phases[0]
    original_deadline = phase.deadline
    
    print(f"📋 Original deadline for '{phase.phase_name}': {original_deadline}")
    
    # Move deadline earlier by 10 days
    new_deadline = original_deadline - timedelta(days=10)
    print(f"🔄 Moving deadline to: {new_deadline}")
    
    result = coordinator.redistribute_tasks_after_deadline_change(phase.id, new_deadline)
    
    print(f"✅ Redistribution result: {result['message']}")
    print(f"📊 Tasks moved: {result['tasks_moved']}")
    
    if result['warnings']:
        print("⚠️  Warnings:")
        for warning in result['warnings']:
            print(f"   - {warning}")
    
    return result

def demonstrate_timeline_visualization(student_id):
    """Demonstrate timeline visualization data"""
    print("\n5️⃣ TIMELINE VISUALIZATION DATA")
    print("-" * 30)
    
    timeline_data = create_timeline_visualization_data(student_id)
    
    print("📊 Summary Statistics:")
    summary = timeline_data['summary']
    print(f"   Total Phases: {summary['total_phases']}")
    print(f"   Phases On Track: {summary['phases_on_track']}")
    print(f"   Critical Phases: {summary['critical_phases']}")
    print(f"   Overall Progress: {summary['overall_progress']:.1f}%")
    print(f"   Total Buffer Days: {summary['total_buffer_days']}")
    
    print(f"\n📅 Timeline Events: {len(timeline_data['timeline_events'])}")
    print(f"📋 Phase Metrics: {len(timeline_data['phase_metrics'])}")
    print(f"🎯 Critical Path Items: {len(timeline_data['critical_path'])}")
    
    # Test JSON serialization
    import json
    json_str = json.dumps(timeline_data, indent=2)
    print(f"\n✅ Data is JSON serializable ({len(json_str)} characters)")
    
    return timeline_data

def main():
    """Main demo function"""
    print("🚀 SCHEDULE COORDINATOR & TIMELINE DEMO")
    print("=" * 60)
    
    with app.app_context():
        # Initialize database
        db.create_all()
        
        # Clean up any existing demo data
        existing_student = Student.query.filter_by(email="demo@timeline.com").first()
        if existing_student:
            print("🧹 Cleaning up existing demo data...")
            # Delete related data
            for phase in existing_student.project_phases:
                PhaseTask.query.filter_by(phase_id=phase.id).delete()
                db.session.delete(phase)
            db.session.delete(existing_student)
            db.session.commit()
        
        # Create fresh demo data
        demo_student = create_demo_data()
        
        # Demonstrate functionality
        coordinator = demonstrate_schedule_coordinator(demo_student.id)
        demonstrate_task_redistribution(coordinator)
        timeline_data = demonstrate_timeline_visualization(demo_student.id)
        
        print("\n" + "="*60)
        print("🎉 DEMO COMPLETE!")
        print("="*60)
        print("\nKey Features Demonstrated:")
        print("✅ Integrated timeline across all phases")
        print("✅ Phase metrics and progress tracking")
        print("✅ Critical path analysis")
        print("✅ Automatic task redistribution")
        print("✅ Timeline visualization data")
        print("✅ JSON serialization for frontend")
        
        print(f"\n💡 Demo student ID: {demo_student.id}")
        print("   You can use this ID to test the timeline routes:")
        print(f"   - GET /timeline (with login)")
        print(f"   - GET /api/timeline/{demo_student.id}")
        print(f"   - POST /api/redistribute_tasks")

if __name__ == '__main__':
    main()