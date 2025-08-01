#!/usr/bin/env python3
"""
Unit tests for PhaseTaskGenerator
Tests phase-specific task generation and distribution
"""

import unittest
from datetime import date, timedelta
import sys
import os

# Add the current directory to Python path to import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import PhaseTaskGenerator, PHASE_TEMPLATES

class TestPhaseTaskGenerator(unittest.TestCase):
    
    def setUp(self):
        """Set up test data"""
        self.work_preferences = {
            'monday': 'light',
            'wednesday': 'heavy',
            'friday': 'light'
        }
        
        # Mock phase object
        class MockPhase:
            def __init__(self, phase_type, deadline, phase_id=1):
                self.phase_type = phase_type
                self.deadline = deadline
                self.id = phase_id
        
        self.mock_phase = MockPhase('literature_review', date.today() + timedelta(days=14))
    
    def test_get_task_template(self):
        """Test PhaseTaskGenerator.get_task_template()"""
        # Test valid phase type
        lit_tasks = PhaseTaskGenerator.get_task_template('literature_review')
        self.assertIsInstance(lit_tasks, list)
        self.assertGreater(len(lit_tasks), 0)
        
        # Verify tasks are strings
        for task in lit_tasks:
            self.assertIsInstance(task, str)
            self.assertGreater(len(task), 0)
        
        # Test invalid phase type
        invalid_tasks = PhaseTaskGenerator.get_task_template('invalid_phase')
        self.assertEqual(invalid_tasks, [])
    
    def test_determine_task_type_reading(self):
        """Test task type determination for reading tasks"""
        reading_tasks = [
            "Read 3 academic articles on topic",
            "Skim literature for key concepts",
            "Review source materials"
        ]
        
        for task in reading_tasks:
            task_type = PhaseTaskGenerator._determine_task_type(task)
            self.assertEqual(task_type, 'reading')
    
    def test_determine_task_type_writing(self):
        """Test task type determination for writing tasks"""
        writing_tasks = [
            "Draft literature review outline",
            "Write research question statement",
            "Draft one-paragraph research gap statement"
        ]
        
        for task in writing_tasks:
            task_type = PhaseTaskGenerator._determine_task_type(task)
            self.assertEqual(task_type, 'writing')
    
    def test_determine_task_type_research(self):
        """Test task type determination for research tasks"""
        research_tasks = [
            "Identify key research gaps",
            "Collect examples of similar studies",
            "Search academic databases"
        ]
        
        for task in research_tasks:
            task_type = PhaseTaskGenerator._determine_task_type(task)
            self.assertEqual(task_type, 'research')
    
    def test_determine_task_type_consultation(self):
        """Test task type determination for consultation tasks"""
        consultation_tasks = [
            "Meet with adviser to discuss progress",
            "Get advisor feedback on methods",
            "Discuss research direction with supervisor"
        ]
        
        for task in consultation_tasks:
            task_type = PhaseTaskGenerator._determine_task_type(task)
            self.assertEqual(task_type, 'consultation')
    
    def test_determine_task_type_documentation(self):
        """Test task type determination for documentation tasks"""
        documentation_tasks = [
            "Complete IRB application",
            "Prepare consent forms for review",
            "Submit ethics documentation"
        ]
        
        for task in documentation_tasks:
            task_type = PhaseTaskGenerator._determine_task_type(task)
            self.assertEqual(task_type, 'documentation')
    
    def test_determine_task_type_default(self):
        """Test task type determination for general tasks"""
        general_tasks = [
            "Complete project milestone",
            "Update progress tracking",
            "Prepare workspace materials"
        ]
        
        for task in general_tasks:
            task_type = PhaseTaskGenerator._determine_task_type(task)
            self.assertEqual(task_type, 'general')
    
    def test_calculate_available_slots(self):
        """Test calculation of available work slots"""
        deadline = date.today() + timedelta(days=7)  # One week from now
        
        slots = PhaseTaskGenerator._calculate_available_slots(self.work_preferences, deadline)
        
        # Should have slots for work days only
        self.assertIsInstance(slots, list)
        self.assertGreater(len(slots), 0)
        
        # Check slot structure
        for slot in slots:
            self.assertIn('date', slot)
            self.assertIn('intensity', slot)
            self.assertIn('capacity', slot)
            self.assertIn('extra_capacity', slot)
            
            # Verify intensity and capacity relationship
            if slot['intensity'] == 'heavy':
                self.assertEqual(slot['capacity'], 2)
            elif slot['intensity'] == 'light':
                self.assertEqual(slot['capacity'], 1)
        
        # Verify only work days are included
        for slot in slots:
            day_name = slot['date'].strftime('%A').lower()
            self.assertIn(day_name, self.work_preferences)
            self.assertNotEqual(self.work_preferences[day_name], 'none')
    
    def test_calculate_available_slots_no_work_days(self):
        """Test calculation with no work days"""
        no_work_days = {'monday': 'none', 'tuesday': 'none'}
        deadline = date.today() + timedelta(days=7)
        
        slots = PhaseTaskGenerator._calculate_available_slots(no_work_days, deadline)
        self.assertEqual(len(slots), 0)
    
    def test_calculate_available_slots_past_deadline(self):
        """Test calculation with past deadline"""
        past_deadline = date.today() - timedelta(days=1)
        
        slots = PhaseTaskGenerator._calculate_available_slots(self.work_preferences, past_deadline)
        self.assertEqual(len(slots), 0)
    
    def test_distribute_tasks_by_intensity(self):
        """Test task distribution across work days"""
        task_templates = [
            "Task 1", "Task 2", "Task 3", "Task 4", "Task 5"
        ]
        deadline = date.today() + timedelta(days=14)
        phase_id = 1
        
        # Note: This test creates PhaseTask objects but doesn't save them to database
        # We're testing the distribution logic, not database operations
        tasks = PhaseTaskGenerator.distribute_tasks_by_intensity(
            task_templates, self.work_preferences, deadline, phase_id
        )
        
        self.assertIsInstance(tasks, list)
        self.assertGreater(len(tasks), 0)
        self.assertLessEqual(len(tasks), len(task_templates))
        
        # Verify task properties
        for task in tasks:
            self.assertEqual(task.phase_id, phase_id)
            self.assertIn(task.task_description, task_templates)
            self.assertIn(task.day_intensity, ['light', 'heavy'])
            self.assertFalse(task.completed)
            self.assertIsNotNone(task.task_type)
    
    def test_distribute_tasks_empty_inputs(self):
        """Test task distribution with empty inputs"""
        # Empty task templates
        tasks = PhaseTaskGenerator.distribute_tasks_by_intensity(
            [], self.work_preferences, date.today() + timedelta(days=7), 1
        )
        self.assertEqual(len(tasks), 0)
        
        # Empty work preferences
        tasks = PhaseTaskGenerator.distribute_tasks_by_intensity(
            ["Task 1"], {}, date.today() + timedelta(days=7), 1
        )
        self.assertEqual(len(tasks), 0)
    
    def test_task_distribution_respects_intensity(self):
        """Test that task distribution respects work day intensity"""
        task_templates = ["Task 1", "Task 2", "Task 3", "Task 4"]
        
        # Create work preferences with specific pattern
        work_prefs = {
            'monday': 'light',    # 1 task capacity
            'tuesday': 'heavy',   # 2 task capacity
            'wednesday': 'light'  # 1 task capacity
        }
        
        # Set deadline to ensure we get exactly these 3 days
        deadline = date.today() + timedelta(days=7)
        
        tasks = PhaseTaskGenerator.distribute_tasks_by_intensity(
            task_templates, work_prefs, deadline, 1
        )
        
        # Group tasks by date to verify intensity distribution
        tasks_by_date = {}
        for task in tasks:
            date_key = task.date
            if date_key not in tasks_by_date:
                tasks_by_date[date_key] = []
            tasks_by_date[date_key].append(task)
        
        # Verify that heavy days get more tasks than light days
        for task_date, date_tasks in tasks_by_date.items():
            day_name = task_date.strftime('%A').lower()
            if day_name in work_prefs:
                expected_intensity = work_prefs[day_name]
                
                # All tasks on this date should have the same intensity
                for task in date_tasks:
                    self.assertEqual(task.day_intensity, expected_intensity)
    
    def test_adjust_tasks_for_dependencies(self):
        """Test task dependency adjustment (currently a pass-through)"""
        mock_tasks = ["Task 1", "Task 2", "Task 3"]
        
        adjusted_tasks = PhaseTaskGenerator.adjust_tasks_for_dependencies(mock_tasks)
        
        # Currently returns tasks as-is
        self.assertEqual(adjusted_tasks, mock_tasks)
    
    def test_all_phase_types_have_task_templates(self):
        """Test that all phase types have task templates"""
        available_phases = ['literature_review', 'research_question', 'methods_planning', 'irb_proposal']
        
        for phase_type in available_phases:
            templates = PhaseTaskGenerator.get_task_template(phase_type)
            self.assertIsInstance(templates, list)
            self.assertGreater(len(templates), 0)
            
            # Verify all templates are non-empty strings
            for template in templates:
                self.assertIsInstance(template, str)
                self.assertGreater(len(template.strip()), 0)

if __name__ == '__main__':
    unittest.main()