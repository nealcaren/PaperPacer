#!/usr/bin/env python3
"""
Integration test for Phase Configuration System
Tests PhaseManager with minimal database interaction
"""

import unittest
import tempfile
import os
from datetime import date, timedelta

from app import app, db, Student, ProjectPhase, PhaseManager

class TestPhaseIntegration(unittest.TestCase):
    
    def setUp(self):
        """Set up test database"""
        self.db_fd, app.config['DATABASE'] = tempfile.mkstemp()
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        
        db.create_all()
        
        # Create test student
        self.student = Student(
            name="Test Student",
            email="test@example.com",
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
        self.assertEqual(phases[0].phase_name, 'Literature Review')
        self.assertEqual(phases[1].phase_name, 'Methods Planning')
        
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
        
        with self.assertRaises(ValueError) as context:
            PhaseManager.create_phases_for_student(
                self.student.id, selected_phases, deadlines
            )
        
        self.assertIn("chronological order", str(context.exception))
    
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
        self.assertEqual(active_phases[0].phase_type, 'literature_review')
        self.assertEqual(active_phases[1].phase_type, 'research_question')
    
    def test_phase_manager_create_all_phases(self):
        """Test creating all available phases"""
        selected_phases = ['literature_review', 'research_question', 'methods_planning', 'irb_proposal']
        deadlines = {
            'literature_review': date.today() + timedelta(days=30),
            'research_question': date.today() + timedelta(days=60),
            'methods_planning': date.today() + timedelta(days=90),
            'irb_proposal': date.today() + timedelta(days=120)
        }
        
        phases = PhaseManager.create_phases_for_student(
            self.student.id, selected_phases, deadlines
        )
        
        self.assertEqual(len(phases), 4)
        
        # Verify all phases have correct order and names
        expected_phases = [
            ('literature_review', 'Literature Review', 1),
            ('research_question', 'Research Question Development', 2),
            ('methods_planning', 'Methods Planning', 3),
            ('irb_proposal', 'IRB Proposal', 4)
        ]
        
        for i, (expected_type, expected_name, expected_order) in enumerate(expected_phases):
            self.assertEqual(phases[i].phase_type, expected_type)
            self.assertEqual(phases[i].phase_name, expected_name)
            self.assertEqual(phases[i].order_index, expected_order)
            self.assertTrue(phases[i].is_active)
            self.assertEqual(phases[i].student_id, self.student.id)

if __name__ == '__main__':
    unittest.main()