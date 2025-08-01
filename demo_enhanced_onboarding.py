#!/usr/bin/env python3
"""
Demonstration of Enhanced Onboarding Flow
Shows multi-phase project creation during onboarding
"""

import tempfile
import os
from datetime import date, timedelta

from app import app, db, Student, ProjectPhase, PhaseTask, PhaseManager

def demo_enhanced_onboarding():
    """Demonstrate the enhanced onboarding system"""
    print("🚀 Enhanced Multi-Phase Onboarding Demo")
    print("=" * 50)
    
    # Set up test database
    db_fd, app.config['DATABASE'] = tempfile.mkstemp()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        
        print("\n📋 Available Research Phases:")
        available_phases = PhaseManager.get_available_phases()
        for phase_type in available_phases:
            template = PhaseManager.get_phase_template(phase_type)
            print(f"  {template['icon']} {template['name']}")
            print(f"     {template['description']}")
            print(f"     Default duration: {template['default_duration_weeks']} weeks")
            print()
        
        # Simulate different onboarding scenarios
        scenarios = [
            {
                'name': 'Literature Review Only',
                'description': 'Traditional single-phase project',
                'phases': ['literature_review'],
                'deadlines': {
                    'literature_review': date.today() + timedelta(days=60)
                }
            },
            {
                'name': 'Comprehensive Research Project',
                'description': 'Full multi-phase research workflow',
                'phases': ['literature_review', 'research_question', 'methods_planning', 'irb_proposal'],
                'deadlines': {
                    'literature_review': date.today() + timedelta(days=30),
                    'research_question': date.today() + timedelta(days=50),
                    'methods_planning': date.today() + timedelta(days=80),
                    'irb_proposal': date.today() + timedelta(days=110)
                }
            },
            {
                'name': 'Methods-Focused Project',
                'description': 'Skipping literature review, focusing on methodology',
                'phases': ['research_question', 'methods_planning'],
                'deadlines': {
                    'research_question': date.today() + timedelta(days=30),
                    'methods_planning': date.today() + timedelta(days=60)
                }
            }
        ]
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n🎯 Scenario {i}: {scenario['name']}")
            print(f"   {scenario['description']}")
            
            # Create student for this scenario
            student = Student(
                name=f"Student {i}",
                email=f"student{i}@example.com",
                project_title=f"Research Project {i}",
                thesis_deadline=date.today() + timedelta(days=180),
                work_days='{"monday": "light", "tuesday": "heavy", "thursday": "light"}',
                onboarded=True,
                is_multi_phase=True
            )
            student.set_password("testpass")
            db.session.add(student)
            db.session.commit()
            
            # Validate phase selection and deadlines
            print(f"   Selected phases: {', '.join(scenario['phases'])}")
            
            is_valid = PhaseManager.validate_phase_deadlines(
                scenario['phases'], scenario['deadlines']
            )
            print(f"   Deadline validation: {'✓ Valid' if is_valid else '✗ Invalid'}")
            
            if not is_valid:
                print(f"   ⚠️  Skipping scenario due to invalid deadlines")
                continue
            
            # Create phases
            phases = PhaseManager.create_phases_for_student(
                student.id, scenario['phases'], scenario['deadlines']
            )
            
            print(f"   Created phases:")
            for phase in phases:
                template = PhaseManager.get_phase_template(phase.phase_type)
                print(f"     {template['icon']} {phase.phase_name} (Order: {phase.order_index})")
                print(f"        Deadline: {phase.deadline}")
            
            # Generate tasks for each phase
            work_preferences = {"monday": "light", "tuesday": "heavy", "thursday": "light"}
            total_tasks = 0
            
            print(f"   Generated tasks:")
            for phase in phases:
                # Generate sample tasks (first 5 for demo)
                template = PhaseManager.get_phase_template(phase.phase_type)
                sample_templates = template['task_templates'][:5]
                
                from app import PhaseTaskGenerator
                tasks = PhaseTaskGenerator.distribute_tasks_by_intensity(
                    sample_templates, work_preferences, phase.deadline, phase.id
                )
                
                for task in tasks:
                    db.session.add(task)
                
                total_tasks += len(tasks)
                print(f"     {phase.phase_name}: {len(tasks)} tasks")
            
            db.session.commit()
            print(f"   Total tasks generated: {total_tasks}")
            
            # Show task distribution by type
            all_tasks = PhaseTask.query.join(ProjectPhase).filter(
                ProjectPhase.student_id == student.id
            ).all()
            
            task_types = {}
            for task in all_tasks:
                task_type = task.task_type
                task_types[task_type] = task_types.get(task_type, 0) + 1
            
            print(f"   Task type distribution:")
            for task_type, count in sorted(task_types.items()):
                print(f"     {task_type}: {count} tasks")
        
        # Summary statistics
        print(f"\n📊 Onboarding Demo Summary:")
        total_students = Student.query.count()
        total_phases = ProjectPhase.query.count()
        total_tasks = PhaseTask.query.count()
        
        print(f"  Students onboarded: {total_students}")
        print(f"  Total phases created: {total_phases}")
        print(f"  Total tasks generated: {total_tasks}")
        
        # Show phase distribution
        phase_counts = {}
        for phase in ProjectPhase.query.all():
            template = PhaseManager.get_phase_template(phase.phase_type)
            phase_name = template['name']
            phase_counts[phase_name] = phase_counts.get(phase_name, 0) + 1
        
        print(f"  Phase distribution:")
        for phase_name, count in sorted(phase_counts.items()):
            print(f"    {phase_name}: {count} instances")
        
        # Demonstrate validation scenarios
        print(f"\n⚠️  Validation Examples:")
        
        validation_tests = [
            {
                'name': 'Valid chronological order',
                'phases': ['literature_review', 'research_question'],
                'deadlines': {
                    'literature_review': date.today() + timedelta(days=30),
                    'research_question': date.today() + timedelta(days=60)
                }
            },
            {
                'name': 'Invalid chronological order',
                'phases': ['literature_review', 'research_question'],
                'deadlines': {
                    'literature_review': date.today() + timedelta(days=60),
                    'research_question': date.today() + timedelta(days=30)  # Before lit review
                }
            },
            {
                'name': 'Past deadline',
                'phases': ['literature_review'],
                'deadlines': {
                    'literature_review': date.today() - timedelta(days=1)  # Past date
                }
            }
        ]
        
        for test in validation_tests:
            is_valid = PhaseManager.validate_phase_deadlines(
                test['phases'], test['deadlines']
            )
            status = '✓ Valid' if is_valid else '✗ Invalid'
            print(f"  {test['name']}: {status}")
        
        print(f"\n🎉 Enhanced Onboarding Demo Complete!")
        print(f"The system successfully:")
        print(f"  ✓ Supports flexible phase selection during onboarding")
        print(f"  ✓ Validates phase deadlines in chronological order")
        print(f"  ✓ Creates phases with proper ordering and metadata")
        print(f"  ✓ Generates phase-specific tasks automatically")
        print(f"  ✓ Handles various research project configurations")
        print(f"  ✓ Provides comprehensive validation and error handling")
    
    # Clean up
    os.close(db_fd)

if __name__ == '__main__':
    demo_enhanced_onboarding()