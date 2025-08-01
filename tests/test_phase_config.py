#!/usr/bin/env python3
"""
Unit tests for Phase Configuration System
Tests PhaseManager and PHASE_TEMPLATES without database dependencies
"""

import unittest
from datetime import date, timedelta
import sys
import os

# Add the current directory to Python path to import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import PhaseManager, PHASE_TEMPLATES

class TestPhaseConfiguration(unittest.TestCase):
    
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
            
            # Verify all task templates are strings
            for task_template in template['task_templates']:
                self.assertIsInstance(task_template, str)
                self.assertGreater(len(task_template), 0)
    
    def test_literature_review_template(self):
        """Test Literature Review phase template specifically"""
        template = PHASE_TEMPLATES['literature_review']
        self.assertEqual(template['name'], 'Literature Review')
        self.assertEqual(template['icon'], '📚')
        self.assertEqual(template['default_duration_weeks'], 4)
        self.assertIn('reading', template['task_types'])
        self.assertIn('note_taking', template['task_types'])
        self.assertIn('synthesis', template['task_types'])
        
        # Check for specific expected tasks
        task_descriptions = template['task_templates']
        self.assertTrue(any('sources' in task.lower() for task in task_descriptions))
        self.assertTrue(any('note-taking' in task.lower() for task in task_descriptions))
    
    def test_research_question_template(self):
        """Test Research Question phase template specifically"""
        template = PHASE_TEMPLATES['research_question']
        self.assertEqual(template['name'], 'Research Question Development')
        self.assertEqual(template['icon'], '❓')
        self.assertEqual(template['default_duration_weeks'], 2)
        self.assertIn('analysis', template['task_types'])
        self.assertIn('writing', template['task_types'])
        self.assertIn('consultation', template['task_types'])
    
    def test_methods_planning_template(self):
        """Test Methods Planning phase template specifically"""
        template = PHASE_TEMPLATES['methods_planning']
        self.assertEqual(template['name'], 'Methods Planning')
        self.assertEqual(template['icon'], '🔬')
        self.assertEqual(template['default_duration_weeks'], 3)
        self.assertIn('design', template['task_types'])
        self.assertIn('planning', template['task_types'])
        self.assertIn('validation', template['task_types'])
    
    def test_irb_proposal_template(self):
        """Test IRB Proposal phase template specifically"""
        template = PHASE_TEMPLATES['irb_proposal']
        self.assertEqual(template['name'], 'IRB Proposal')
        self.assertEqual(template['icon'], '📋')
        self.assertEqual(template['default_duration_weeks'], 2)
        self.assertIn('documentation', template['task_types'])
        self.assertIn('compliance', template['task_types'])
        self.assertIn('submission', template['task_types'])
    
    def test_phase_manager_get_available_phases(self):
        """Test PhaseManager.get_available_phases()"""
        available_phases = PhaseManager.get_available_phases()
        self.assertIsInstance(available_phases, list)
        self.assertIn('literature_review', available_phases)
        self.assertIn('research_question', available_phases)
        self.assertIn('methods_planning', available_phases)
        self.assertIn('irb_proposal', available_phases)
        self.assertEqual(len(available_phases), 4)
    
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
    
    def test_phase_manager_validate_deadlines_same_date(self):
        """Test PhaseManager.validate_phase_deadlines() with same dates"""
        same_date = date.today() + timedelta(days=30)
        selected_phases = ['literature_review', 'research_question']
        deadlines = {
            'literature_review': same_date,
            'research_question': same_date  # Same date should be invalid
        }
        
        self.assertFalse(PhaseManager.validate_phase_deadlines(selected_phases, deadlines))
    
    def test_phase_manager_validate_deadlines_empty_inputs(self):
        """Test PhaseManager.validate_phase_deadlines() with empty inputs"""
        self.assertFalse(PhaseManager.validate_phase_deadlines([], {}))
        self.assertFalse(PhaseManager.validate_phase_deadlines(['literature_review'], {}))
        self.assertFalse(PhaseManager.validate_phase_deadlines([], {'literature_review': date.today() + timedelta(days=30)}))
    
    def test_phase_manager_validate_deadlines_missing_deadline(self):
        """Test PhaseManager.validate_phase_deadlines() with missing deadline"""
        selected_phases = ['literature_review', 'research_question']
        deadlines = {
            'literature_review': date.today() + timedelta(days=30)
            # Missing research_question deadline
        }
        
        self.assertFalse(PhaseManager.validate_phase_deadlines(selected_phases, deadlines))
    
    def test_phase_manager_validate_deadlines_logical_order(self):
        """Test PhaseManager.validate_phase_deadlines() respects logical phase order"""
        # Test all phases in correct order
        selected_phases = ['literature_review', 'research_question', 'methods_planning', 'irb_proposal']
        deadlines = {
            'literature_review': date.today() + timedelta(days=30),
            'research_question': date.today() + timedelta(days=60),
            'methods_planning': date.today() + timedelta(days=90),
            'irb_proposal': date.today() + timedelta(days=120)
        }
        
        self.assertTrue(PhaseManager.validate_phase_deadlines(selected_phases, deadlines))
        
        # Test skipping phases (should still work if in order)
        selected_phases = ['literature_review', 'methods_planning', 'irb_proposal']
        deadlines = {
            'literature_review': date.today() + timedelta(days=30),
            'methods_planning': date.today() + timedelta(days=60),
            'irb_proposal': date.today() + timedelta(days=90)
        }
        
        self.assertTrue(PhaseManager.validate_phase_deadlines(selected_phases, deadlines))
        
        # Test out of logical order (should fail)
        selected_phases = ['methods_planning', 'literature_review']  # Wrong order
        deadlines = {
            'methods_planning': date.today() + timedelta(days=30),
            'literature_review': date.today() + timedelta(days=60)
        }
        
        self.assertFalse(PhaseManager.validate_phase_deadlines(selected_phases, deadlines))

if __name__ == '__main__':
    unittest.main()