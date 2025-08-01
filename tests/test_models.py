#!/usr/bin/env python3
"""
Unit tests for PaperPacer database models
Tests the new multi-phase models and relationships
"""

import unittest
import tempfile
import os
from datetime import datetime, date, timedelta

from app import app, db, Student, ProjectPhase, PhaseTask, PhaseType, PhaseManager, PHASE_TEMPLATES

class TestMultiPhaseModels(unittest.TestCase):
    
    def setUp(self):
        """Set up test database"""
        self.db_fd, app.config['DATABASE'] = tempfile.mkstemp()
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        
        db.create_all()
        
        # Create test student with unique email
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        self.student = Student(
            name="Test Student",
            email=f"test-{unique_id}@example.com",
            project_title="Test Project",
            thesis_deadline=date.today() + timedelta(days=180),
            lit_review_deadline=date.today() + timedelta(days=90),
            work_days='{"monday": "light", "wednesday": "heavy"}',
            onboarded=True,
            is_multi_phase=True
        )
        self.student.set_password("testpass")
        db.session.add(self.student)
        db.session.commit()
    
    def tearDown(self):
        """Clean up test database"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        os.close(self.db_fd)
    
    def test_phase_type_enum(self):
        """Test PhaseType enumeration"""
        self.assertEqual(PhaseType.LITERATURE_REVIEW.value, "literature_review")
        self.assertEqual(PhaseType.RESEARCH_QUESTION.value, "research_question")
        self.assertEqual(PhaseType.METHODS_PLANNING.value, "methods_planning")
        self.assertEqual(PhaseType.IRB_PROPOSAL.value, "irb_proposal")
    
    def test_project_phase_creation(self):
        """Test ProjectPhase model creation and relationships"""
        phase = ProjectPhase(
            student_id=self.student.id,
            phase_type=PhaseType.LITERATURE_REVIEW.value,
            phase_name="Literature Review",
            deadline=date.today() + timedelta(days=60),
            is_active=True,
            order_index=1
        )
        
        db.session.add(phase)
        db.session.commit()
        
        # Test phase was created
        self.assertIsNotNone(phase.id)
        self.assertEqual(phase.student_id, self.student.id)
        self.assertEqual(phase.phase_type, "literature_review")
        self.assertEqual(phase.phase_name, "Literature Review")
        self.assertTrue(phase.is_active)
        
        # Test relationship with student
        self.assertIn(phase, self.student.project_phases)
        self.assertEqual(phase.student, self.student)
    
    def test_phase_task_creation(self):
        """Test PhaseTask model creation and relationships"""
        # Create a phase first
        phase = ProjectPhase(
            student_id=self.student.id,
            phase_type=PhaseType.LITERATURE_REVIEW.value,
            phase_name="Literature Review",
            deadline=date.today() + timedelta(days=60),
            order_index=1
        )
        db.session.add(phase)
        db.session.commit()
        
        # Create a task for the phase
        task = PhaseTask(
            phase_id=phase.id,
            date=date.today() + timedelta(days=1),
            task_description="Read 3 academic articles on topic",
            task_type="reading",
            day_intensity="light",
            completed=False
        )
        
        db.session.add(task)
        db.session.commit()
        
        # Test task was created
        self.assertIsNotNone(task.id)
        self.assertEqual(task.phase_id, phase.id)
        self.assertEqual(task.task_type, "reading")
        self.assertEqual(task.day_intensity, "light")
        self.assertFalse(task.completed)
        
        # Test relationships
        self.assertEqual(task.project_phase, phase)
        self.assertIn(task, phase.phase_tasks)
        
        # Test computed student_id property
        self.assertEqual(task.student_id, self.student.id)
    
    def test_student_multi_phase_flag(self):
        """Test Student model multi-phase flag"""
        self.assertTrue(self.student.is_multi_phase)
        
        # Create legacy student
        legacy_student = Student(
            name="Legacy Student",
            email="legacy@example.com",
            is_multi_phase=False
        )
        legacy_student.set_password("testpass")
        db.session.add(legacy_student)
        db.session.commit()
        
        self.assertFalse(legacy_student.is_multi_phase)
    
    def test_cascade_delete_phases(self):
        """Test that deleting a student cascades to phases and tasks"""
        # Create phase and task
        phase = ProjectPhase(
            student_id=self.student.id,
            phase_type=PhaseType.RESEARCH_QUESTION.value,
            phase_name="Research Question",
            deadline=date.today() + timedelta(days=30),
            order_index=2
        )
        db.session.add(phase)
        db.session.commit()
        
        task = PhaseTask(
            phase_id=phase.id,
            date=date.today() + timedelta(days=5),
            task_description="Draft research question",
            task_type="writing"
        )
        db.session.add(task)
        db.session.commit()
        
        phase_id = phase.id
        task_id = task.id
        
        # Delete student
        db.session.delete(self.student)
        db.session.commit()
        
        # Verify cascade delete worked
        self.assertIsNone(ProjectPhase.query.get(phase_id))
        self.assertIsNone(PhaseTask.query.get(task_id))
    
    def test_cascade_delete_tasks(self):
        """Test that deleting a phase cascades to tasks"""
        # Create phase and task
        phase = ProjectPhase(
            student_id=self.student.id,
            phase_type=PhaseType.METHODS_PLANNING.value,
            phase_name="Methods Planning",
            deadline=date.today() + timedelta(days=45),
            order_index=3
        )
        db.session.add(phase)
        db.session.commit()
        
        task = PhaseTask(
            phase_id=phase.id,
            date=date.today() + timedelta(days=10),
            task_description="Design survey instrument",
            task_type="design"
        )
        db.session.add(task)
        db.session.commit()
        
        task_id = task.id
        
        # Delete phase
        db.session.delete(phase)
        db.session.commit()
        
        # Verify task was deleted
        self.assertIsNone(PhaseTask.query.get(task_id))
    
    def test_phase_ordering(self):
        """Test phase ordering with order_index"""
        # Create phases in different order
        phase2 = ProjectPhase(
            student_id=self.student.id,
            phase_type=PhaseType.RESEARCH_QUESTION.value,
            phase_name="Research Question",
            deadline=date.today() + timedelta(days=30),
            order_index=2
        )
        
        phase1 = ProjectPhase(
            student_id=self.student.id,
            phase_type=PhaseType.LITERATURE_REVIEW.value,
            phase_name="Literature Review",
            deadline=date.today() + timedelta(days=60),
            order_index=1
        )
        
        db.session.add_all([phase2, phase1])
        db.session.commit()
        
        # Query phases ordered by order_index
        ordered_phases = ProjectPhase.query.filter_by(
            student_id=self.student.id
        ).order_by(ProjectPhase.order_index).all()
        
        self.assertEqual(len(ordered_phases), 2)
        self.assertEqual(ordered_phases[0].order_index, 1)
        self.assertEqual(ordered_phases[1].order_index, 2)
        self.assertEqual(ordered_phases[0].phase_type, "literature_review")
        self.assertEqual(ordered_phases[1].phase_type, "research_question")
    
    def test_phase_templates_configuration(self):
        """Test PHASE_TEMPLATES configuration"""
        # Test that all expected phases are defined
        expected_phases = ['literature_review', 'research_question', 'methods_planning', 'irb_proposal']
        for phase_type in expected_phases:
            self.assertIn(phase_type, PHASE_TEMPLATES)
            
            template = PHASE_TEMPLATES[phase_type]
            self.assertIn('name', template)
            self.assertIn('description', template)
            self.assertIn('icon', template)
            self.assertIn('default_duration_weeks', template)
            self.assertIn('task_types', template)
            self.assertIn('task_templates', template)
            
            # Verify task templates are not empty
            self.assertGreater(len(template['task_templates']), 0)
    
    def test_phase_manager_get_available_phases(self):
        """Test PhaseManager.get_available_phases()"""
        available_phases = PhaseManager.get_available_phases()
        self.assertIsInstance(available_phases, list)
        self.assertIn('literature_review', available_phases)
        self.assertIn('research_question', available_phases)
        self.assertIn('methods_planning', available_phases)
        self.assertIn('irb_proposal', available_phases)
    
    def test_phase_manager_get_phase_template(self):
        """Test PhaseManager.get_phase_template()"""
        template = PhaseManager.get_phase_template('literature_review')
        self.assertIsNotNone(template)
        self.assertEqual(template['name'], 'Literature Review')
        self.assertEqual(template['icon'], '📚')
        
        # Test invalid phase type
        invalid_template = PhaseManager.get_phase_template('invalid_phase')
        self.assertIsNone(invalid_template)
    
    def test_phase_manager_validate_deadlines_valid(self):
        """Test PhaseManager.validate_phase_deadlines() with valid deadlines"""
        selected_phases = ['literature_review', 'research_question']
        deadlines = {
            'literature_review': date.today() + timedelta(days=30),
            'research_question': date.today() + timedelta(days=60)
        }
        
        self.assertTrue(PhaseManager.validate_phase_deadlines(selected_phases, deadlines))
    
    def test_phase_manager_validate_deadlines_invalid_order(self):
        """Test PhaseManager.validate_phase_deadlines() with invalid chronological order"""
        selected_phases = ['literature_review', 'research_question']
        deadlines = {
            'literature_review': date.today() + timedelta(days=60),
            'research_question': date.today() + timedelta(days=30)  # Before lit review
        }
        
        self.assertFalse(PhaseManager.validate_phase_deadlines(selected_phases, deadlines))
    
    def test_phase_manager_validate_deadlines_past_dates(self):
        """Test PhaseManager.validate_phase_deadlines() with past dates"""
        selected_phases = ['literature_review']
        deadlines = {
            'literature_review': date.today() - timedelta(days=1)  # Past date
        }
        
        self.assertFalse(PhaseManager.validate_phase_deadlines(selected_phases, deadlines))
    
    def test_phase_manager_create_phases_for_student(self):
        """Test PhaseManager.create_phases_for_student()"""
        selected_phases = ['literature_review', 'methods_planning']
        deadlines = {
            'literature_review': date.today() + timedelta(days=30),
            'methods_planning': date.today() + timedelta(days=60)
        }
        
        phases = PhaseManager.create_phases_for_student(
            self.student.id, selected_phases, deadlines
        )
        
        self.assertEqual(len(phases), 2)
        self.assertEqual(phases[0].phase_type, 'literature_review')
        self.assertEqual(phases[1].phase_type, 'methods_planning')
        self.assertEqual(phases[0].order_index, 1)
        self.assertEqual(phases[1].order_index, 2)
        
        # Verify phases were saved to database
        db_phases = ProjectPhase.query.filter_by(student_id=self.student.id).all()
        self.assertEqual(len(db_phases), 2)
    
    def test_phase_manager_create_phases_invalid_deadlines(self):
        """Test PhaseManager.create_phases_for_student() with invalid deadlines"""
        selected_phases = ['literature_review', 'research_question']
        deadlines = {
            'literature_review': date.today() + timedelta(days=60),
            'research_question': date.today() + timedelta(days=30)  # Invalid order
        }
        
        with self.assertRaises(ValueError):
            PhaseManager.create_phases_for_student(
                self.student.id, selected_phases, deadlines
            )
    
    def test_phase_manager_get_active_phases(self):
        """Test PhaseManager.get_active_phases()"""
        # Create test phases
        phase1 = ProjectPhase(
            student_id=self.student.id,
            phase_type='research_question',
            phase_name='Research Question',
            deadline=date.today() + timedelta(days=30),
            order_index=2,
            is_active=True
        )
        
        phase2 = ProjectPhase(
            student_id=self.student.id,
            phase_type='literature_review',
            phase_name='Literature Review',
            deadline=date.today() + timedelta(days=60),
            order_index=1,
            is_active=True
        )
        
        phase3 = ProjectPhase(
            student_id=self.student.id,
            phase_type='methods_planning',
            phase_name='Methods Planning',
            deadline=date.today() + timedelta(days=90),
            order_index=3,
            is_active=False  # Inactive
        )
        
        db.session.add_all([phase1, phase2, phase3])
        db.session.commit()
        
        active_phases = PhaseManager.get_active_phases(self.student.id)
        
        # Should return only active phases, ordered by order_index
        self.assertEqual(len(active_phases), 2)
        self.assertEqual(active_phases[0].order_index, 1)  # Literature Review first
        self.assertEqual(active_phases[1].order_index, 2)  # Research Question second
    
    def test_phase_manager_get_phase_progress(self):
        """Test PhaseManager.get_phase_progress()"""
        # Create a phase with tasks
        phase = ProjectPhase(
            student_id=self.student.id,
            phase_type='literature_review',
            phase_name='Literature Review',
            deadline=date.today() + timedelta(days=30),
            order_index=1
        )
        db.session.add(phase)
        db.session.commit()
        
        # Add tasks (2 completed, 3 total)
        task1 = PhaseTask(
            phase_id=phase.id,
            date=date.today() + timedelta(days=1),
            task_description="Task 1",
            completed=True
        )
        task2 = PhaseTask(
            phase_id=phase.id,
            date=date.today() + timedelta(days=2),
            task_description="Task 2",
            completed=True
        )
        task3 = PhaseTask(
            phase_id=phase.id,
            date=date.today() + timedelta(days=3),
            task_description="Task 3",
            completed=False
        )
        
        db.session.add_all([task1, task2, task3])
        db.session.commit()
        
        progress = PhaseManager.get_phase_progress(phase.id)
        
        self.assertIsNotNone(progress)
        self.assertEqual(progress['total_tasks'], 3)
        self.assertEqual(progress['completed_tasks'], 2)
        self.assertEqual(progress['progress_percentage'], 66.7)
        self.assertFalse(progress['is_complete'])
        self.assertEqual(progress['phase'], phase)

if __name__ == '__main__':
    unittest.main()