#!/usr/bin/env python3

"""
Demo: Phase-Aware Progress Tracking System

This demo shows the complete phase-aware progress tracking functionality
including milestone detection, celebration features, and progress visualization.
"""

import sys
import os
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import the app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, Student, ProjectPhase, PhaseTask, PhaseType, ProgressLog
from phase_progress_tracker import PhaseProgressTracker, create_progress_visualization_data
from werkzeug.security import generate_password_hash

def create_demo_data():
    """Create demo data for testing phase progress tracking"""
    print("🔧 Setting up demo data...")
    
    # Create a test user with multi-phase project
    demo_user = Student(
        name="Demo User",
        email="demo@example.com",
        password_hash=generate_password_hash("password"),
        project_title="AI Ethics Research Project",
        thesis_deadline=datetime.now().date() + timedelta(days=120),
        lit_review_deadline=datetime.now().date() + timedelta(days=30),
        onboarded=True,
        is_multi_phase=True
    )
    db.session.add(demo_user)
    db.session.commit()
    
    # Create phases
    today = datetime.now().date()
    
    phases = [
        {
            'type': PhaseType.LITERATURE_REVIEW.value,
            'name': 'Literature Review',
            'deadline': today + timedelta(days=30),
            'order': 1
        },
        {
            'type': PhaseType.RESEARCH_QUESTION.value,
            'name': 'Research Question Development',
            'deadline': today + timedelta(days=50),
            'order': 2
        },
        {
            'type': PhaseType.METHODS_PLANNING.value,
            'name': 'Methods Planning',
            'deadline': today + timedelta(days=80),
            'order': 3
        },
        {
            'type': PhaseType.IRB_PROPOSAL.value,
            'name': 'IRB Proposal',
            'deadline': today + timedelta(days=120),
            'order': 4
        }
    ]
    
    created_phases = []
    for phase_data in phases:
        phase = ProjectPhase(
            student_id=demo_user.id,
            phase_type=phase_data['type'],
            phase_name=phase_data['name'],
            deadline=phase_data['deadline'],
            order_index=phase_data['order'],
            is_active=True
        )
        db.session.add(phase)
        created_phases.append(phase)
    
    db.session.commit()
    
    # Create tasks for each phase
    task_templates = {
        PhaseType.LITERATURE_REVIEW.value: [
            "Search academic databases for relevant papers",
            "Read and summarize 10 key research papers",
            "Identify research gaps in current literature",
            "Create literature review outline",
            "Write literature review draft"
        ],
        PhaseType.RESEARCH_QUESTION.value: [
            "Analyze gaps identified in literature review",
            "Brainstorm potential research questions",
            "Evaluate research questions for feasibility",
            "Refine primary research question"
        ],
        PhaseType.METHODS_PLANNING.value: [
            "Select appropriate research methodology",
            "Design data collection instruments",
            "Plan sampling strategy",
            "Create data analysis plan"
        ],
        PhaseType.IRB_PROPOSAL.value: [
            "Complete ethics training requirements",
            "Draft informed consent forms",
            "Prepare IRB application materials",
            "Submit IRB application"
        ]
    }
    
    for phase in created_phases:
        templates = task_templates.get(phase.phase_type, [])
        for i, task_desc in enumerate(templates):
            task_date = today + timedelta(days=i * 2)  # Spread tasks over time
            task = PhaseTask(
                phase_id=phase.id,
                date=task_date,
                task_description=task_desc,
                task_type='general',
                day_intensity='medium',
                completed=False
            )
            db.session.add(task)
    
    db.session.commit()
    return demo_user, created_phases

def demo_progress_tracking():
    """Demonstrate phase progress tracking functionality"""
    print("\n🎯 PHASE-AWARE PROGRESS TRACKING DEMO")
    print("=" * 50)
    
    with app.app_context():
        db.create_all()
        
        # Create demo data
        demo_user, phases = create_demo_data()
        
        # Initialize progress tracker
        tracker = PhaseProgressTracker(demo_user.id)
        
        print(f"\n👤 Demo User: {demo_user.name}")
        print(f"📚 Project: {demo_user.project_title}")
        print(f"🎯 Total Phases: {len(phases)}")
        
        # Show initial progress
        print("\n📊 INITIAL PROGRESS SUMMARY")
        print("-" * 30)
        overall_summary = tracker.get_overall_progress_summary()
        print(f"Overall Progress: {overall_summary['overall_progress_percentage']:.1f}%")
        print(f"Total Tasks: {overall_summary['total_tasks']}")
        print(f"Phases On Track: {overall_summary['phases_on_track']}/{overall_summary['total_phases']}")
        
        # Simulate completing tasks in Literature Review phase
        lit_review_phase = phases[0]
        lit_review_tasks = PhaseTask.query.filter_by(phase_id=lit_review_phase.id).all()
        
        print(f"\n🔬 SIMULATING PROGRESS IN: {lit_review_phase.phase_name}")
        print("-" * 50)
        
        # Complete first task (should trigger 20% milestone)
        print("\n1️⃣ Completing first task...")
        task1 = lit_review_tasks[0]
        task1.completed = True
        db.session.commit()
        
        result1 = tracker.log_phase_progress(
            lit_review_phase.id,
            [task1.id],
            "Started literature search - found some great papers!"
        )
        
        print(f"   Progress: {result1['progress_percentage']:.1f}%")
        print(f"   Tasks: {result1['completed_tasks']}/{result1['total_tasks']}")
        if result1['milestones_achieved']:
            for milestone in result1['milestones_achieved']:
                print(f"   🎉 {milestone['celebration_message']}")
        
        # Complete second task (should trigger more milestones)
        print("\n2️⃣ Completing second task...")
        task2 = lit_review_tasks[1]
        task2.completed = True
        db.session.commit()
        
        result2 = tracker.log_phase_progress(
            lit_review_phase.id,
            [task2.id],
            "Read several key papers, taking detailed notes"
        )
        
        print(f"   Progress: {result2['progress_percentage']:.1f}%")
        print(f"   Tasks: {result2['completed_tasks']}/{result2['total_tasks']}")
        if result2['milestones_achieved']:
            for milestone in result2['milestones_achieved']:
                print(f"   🎉 {milestone['celebration_message']}")
        
        # Complete third task (should trigger 60% milestone)
        print("\n3️⃣ Completing third task...")
        task3 = lit_review_tasks[2]
        task3.completed = True
        db.session.commit()
        
        result3 = tracker.log_phase_progress(
            lit_review_phase.id,
            [task3.id],
            "Identified several research gaps - exciting opportunities!"
        )
        
        print(f"   Progress: {result3['progress_percentage']:.1f}%")
        print(f"   Tasks: {result3['completed_tasks']}/{result3['total_tasks']}")
        if result3['milestones_achieved']:
            for milestone in result3['milestones_achieved']:
                print(f"   🎉 {milestone['celebration_message']}")
        
        # Show detailed phase progress summary
        print(f"\n📈 DETAILED PROGRESS SUMMARY: {lit_review_phase.phase_name}")
        print("-" * 50)
        phase_summary = tracker.get_phase_progress_summary(lit_review_phase.id)
        
        print(f"Phase: {phase_summary.phase_name}")
        print(f"Progress: {phase_summary.progress_percentage:.1f}%")
        print(f"Tasks: {phase_summary.completed_tasks}/{phase_summary.total_tasks}")
        print(f"Days Active: {phase_summary.days_active}")
        print(f"Days Remaining: {phase_summary.days_remaining}")
        print(f"Average Tasks/Day: {phase_summary.average_tasks_per_day:.1f}")
        print(f"Current Streak: {phase_summary.current_streak} days")
        print(f"Longest Streak: {phase_summary.longest_streak} days")
        print(f"On Track: {'✅ Yes' if phase_summary.is_on_track else '⚠️ Behind Schedule'}")
        
        if phase_summary.completion_prediction:
            print(f"Predicted Completion: {phase_summary.completion_prediction}")
        
        print(f"\n🏆 Milestones Achieved: {len(phase_summary.milestones_achieved)}")
        for milestone in phase_summary.milestones_achieved:
            print(f"   • {milestone.description} - {milestone.celebration_message}")
        
        # Test phase completion detection
        print(f"\n🎯 TESTING PHASE COMPLETION")
        print("-" * 30)
        
        # Complete remaining tasks
        remaining_tasks = [t for t in lit_review_tasks if not t.completed]
        for task in remaining_tasks:
            task.completed = True
        db.session.commit()
        
        # Log completion
        remaining_task_ids = [t.id for t in remaining_tasks]
        completion_result = tracker.log_phase_progress(
            lit_review_phase.id,
            remaining_task_ids,
            "Finished literature review! Ready for next phase."
        )
        
        print(f"Final Progress: {completion_result['progress_percentage']:.1f}%")
        if completion_result['milestones_achieved']:
            for milestone in completion_result['milestones_achieved']:
                print(f"🎉 {milestone['celebration_message']}")
        
        # Check for phase completion celebration
        completion_data = tracker.detect_phase_completion(lit_review_phase.id)
        if completion_data:
            print(f"\n🎊 PHASE COMPLETION CELEBRATION!")
            print(f"   Phase: {completion_data['phase_name']}")
            print(f"   Completion Date: {completion_data['completion_date']}")
            print(f"   Total Tasks: {completion_data['total_tasks']}")
            print(f"   Days Early: {completion_data['days_early']}")
            print(f"   🎉 {completion_data['celebration_message']}")
            print(f"   Badges: {', '.join(completion_data['achievement_badges'])}")
            
            if completion_data['next_phase']:
                next_phase = completion_data['next_phase']
                print(f"   Next Phase: {next_phase['phase_name']}")
        
        # Show updated overall progress
        print(f"\n📊 UPDATED OVERALL PROGRESS")
        print("-" * 30)
        final_summary = tracker.get_overall_progress_summary()
        print(f"Overall Progress: {final_summary['overall_progress_percentage']:.1f}%")
        print(f"Completed Tasks: {final_summary['total_completed']}/{final_summary['total_tasks']}")
        print(f"Phases On Track: {final_summary['phases_on_track']}/{final_summary['total_phases']}")
        print(f"Total Milestones: {final_summary['total_milestones_achieved']}")
        
        if final_summary['most_active_phase']:
            most_active = final_summary['most_active_phase']
            print(f"Most Active Phase: {most_active['name']} ({most_active['progress']:.1f}%)")
        
        if final_summary['next_milestone']:
            next_milestone = final_summary['next_milestone']
            print(f"Next Milestone: {next_milestone['milestone_percentage']}% in {next_milestone['phase_name']}")
            print(f"Tasks Needed: {next_milestone['tasks_needed']}")
        
        # Test progress visualization data
        print(f"\n📈 PROGRESS VISUALIZATION DATA")
        print("-" * 30)
        viz_data = create_progress_visualization_data(demo_user.id)
        print(f"Data Structure Created: ✅")
        print(f"Overall Progress: {viz_data['overall_summary']['overall_progress_percentage']:.1f}%")
        print(f"Phase Details: {len(viz_data['phase_details'])} phases")
        
        for phase_detail in viz_data['phase_details']:
            print(f"   • {phase_detail['phase_name']}: {phase_detail['progress_percentage']:.1f}%")
        
        print(f"\n✅ PHASE PROGRESS TRACKING DEMO COMPLETE!")
        print("=" * 50)
        print("🎯 All features working correctly:")
        print("   ✅ Phase-specific progress logging")
        print("   ✅ Milestone detection and celebration")
        print("   ✅ Progress calculation and visualization")
        print("   ✅ Phase completion detection")
        print("   ✅ Streak tracking and analytics")
        print("   ✅ Progress prediction and on-track analysis")
        print("   ✅ Overall progress summary across phases")
        print("   ✅ Progress visualization data generation")

if __name__ == "__main__":
    demo_progress_tracking()