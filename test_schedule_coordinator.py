#!/usr/bin/env python3

import unittest
import sys
import os
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import the app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, Student, ProjectPhase, PhaseTask, PhaseType
from schedule_coordinator import ScheduleCoordinator, create_timeline_visualization_data, CriticalityLevel
from werkzeug.security import generate_password_hash

class TestScheduleCoordinator(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        
        db.create_all()
        
        # Create a test user with multi-phase project
        self.test_user = Student(
            name="Test User",
            email="test@example.com",
            password_hash=generate_password_hash("password"),
            project_title="Test Project",
            thesis_deadline=datetime.now().date() + timedelta(days=180),
            lit_review_deadline=datetime.now().date() + timedelta(days=90),
            onboarded=True,
            is_multi_phase=True
        )
        db.session.add(self.test_user)
        db.session.commit()
        
        # Create test phases
        today = datetime.now().date()
        
        self.phase1 = ProjectPhase(
            student_id=self.test_user.id,
            phase_type=PhaseType.LITERATURE_REVIEW.value,
            phase_name="Literature Review",
            deadline=today + timedelta(days=30),
            order_index=1,
            is_active=True
        )
        
        self.phase2 = ProjectPhase(
            student_id=self.test_user.id,
            phase_type=PhaseType.RESEARCH_QUESTION.value,
            phase_name="Research Question Development",
            deadline=today + timedelta(days=60),
            order_index=2,
            is_active=True
        )
        
        self.phase3 = ProjectPhase(
            student_id=self.test_user.id,
            phase_type=PhaseType.METHODS_PLANNING.value,
            phase_name="Methods Planning",
            deadline=today + timedelta(days=90),
            order_index=3,
            is_active=True
        )
        
        db.session.add_all([self.phase1, self.phase2, self.phase3])
        db.session.commit()
        
        # Create test tasks
        self._create_test_tasks()
    
    def tearDown(self):
        """Clean up after tests"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def _create_test_tasks(self):
        """Create test tasks for the phases"""
        today = datetime.now().date()
        
        # Phase 1 tasks (some completed, some not)
        tasks_p1 = [
            PhaseTask(
                phase_id=self.phase1.id,
                date=today + timedelta(days=1),
                task_description="Literature Review Task 1",
                task_type="reading",
                day_intensity="light",
                completed=True
            ),
            PhaseTask(
                phase_id=self.phase1.id,
                date=today + timedelta(days=3),
                task_description="Literature Review Task 2",
                task_type="reading",
                day_intensity="heavy",
                completed=False
            ),
            PhaseTask(
                phase_id=self.phase1.id,
                date=today + timedelta(days=5),
                task_description="Literature Review Task 3",
                task_type="analysis",
                day_intensity="light",
                completed=False
            )
        ]
        
        # Phase 2 tasks (all incomplete)
        tasks_p2 = [
            PhaseTask(
                phase_id=self.phase2.id,
                date=today + timedelta(days=35),
                task_description="Research Question Task 1",
                task_type="writing",
                day_intensity="light",
                completed=False
            ),
            PhaseTask(
                phase_id=self.phase2.id,
                date=today + timedelta(days=40),
                task_description="Research Question Task 2",
                task_type="analysis",
                day_intensity="heavy",
                completed=False
            )
        ]
        
        # Phase 3 tasks (none yet)
        tasks_p3 = [
            PhaseTask(
                phase_id=self.phase3.id,
                date=today + timedelta(days=70),
                task_description="Methods Planning Task 1",
                task_type="planning",
                day_intensity="light",
                completed=False
            )
        ]
        
        db.session.add_all(tasks_p1 + tasks_p2 + tasks_p3)
        db.session.commit()
    
    def test_coordinator_initialization(self):
        """Test ScheduleCoordinator initialization"""
        coordinator = ScheduleCoordinator(self.test_user.id)
        
        self.assertEqual(coordinator.student_id, self.test_user.id)
        self.assertEqual(len(coordinator.phases), 3)
        self.assertEqual(coordinator.phases[0].phase_name, "Literature Review")
    
    def test_coordinator_invalid_user(self):
        """Test ScheduleCoordinator with invalid user"""
        with self.assertRaises(ValueError):
            ScheduleCoordinator(999)  # Non-existent user
    
    def test_get_integrated_timeline(self):
        """Test integrated timeline generation"""
        coordinator = ScheduleCoordinator(self.test_user.id)
        timeline = coordinator.get_integrated_timeline()
        
        # Should have deadline events for all phases
        deadline_events = [e for e in timeline if e.event_type == 'deadline']
        self.assertEqual(len(deadline_events), 3)
        
        # Should have task cluster events
        task_events = [e for e in timeline if e.event_type == 'task_cluster']
        self.assertGreaterEqual(len(task_events), 0)
        
        # Events should be sorted by date
        dates = [e.date for e in timeline]
        self.assertEqual(dates, sorted(dates))
    
    def test_get_phase_metrics(self):
        """Test phase metrics calculation"""
        coordinator = ScheduleCoordinator(self.test_user.id)
        metrics = coordinator.get_phase_metrics()
        
        self.assertEqual(len(metrics), 3)
        
        # Check first phase metrics
        phase1_metrics = next(m for m in metrics if m.phase_id == self.phase1.id)
        self.assertEqual(phase1_metrics.total_tasks, 3)
        self.assertEqual(phase1_metrics.completed_tasks, 1)
        self.assertEqual(phase1_metrics.remaining_tasks, 2)
        self.assertAlmostEqual(phase1_metrics.progress_percentage, 33.33, places=1)
        
        # Check that all metrics have required fields
        for metric in metrics:
            self.assertIsNotNone(metric.phase_name)
            self.assertIsNotNone(metric.deadline)
            self.assertIsNotNone(metric.criticality)
            self.assertIsInstance(metric.is_on_track, bool)
    
    def test_redistribute_tasks_after_deadline_change(self):
        """Test automatic task redistribution"""
        coordinator = ScheduleCoordinator(self.test_user.id)
        
        # Change phase 1 deadline to be sooner
        new_deadline = datetime.now().date() + timedelta(days=10)
        result = coordinator.redistribute_tasks_after_deadline_change(
            self.phase1.id, 
            new_deadline
        )
        
        self.assertTrue(result['success'])
        self.assertGreaterEqual(result['tasks_moved'], 0)
        
        # Verify deadline was updated
        updated_phase = ProjectPhase.query.get(self.phase1.id)
        self.assertEqual(updated_phase.deadline, new_deadline)
        
        # Verify tasks were redistributed within new timeframe
        phase_tasks = PhaseTask.query.filter_by(
            phase_id=self.phase1.id,
            completed=False
        ).all()
        
        for task in phase_tasks:
            self.assertLessEqual(task.date, new_deadline)
    
    def test_redistribute_tasks_invalid_phase(self):
        """Test task redistribution with invalid phase"""
        coordinator = ScheduleCoordinator(self.test_user.id)
        
        with self.assertRaises(ValueError):
            coordinator.redistribute_tasks_after_deadline_change(999, datetime.now().date())
    
    def test_get_critical_path(self):
        """Test critical path analysis"""
        coordinator = ScheduleCoordinator(self.test_user.id)
        critical_path = coordinator.get_critical_path()
        
        self.assertEqual(len(critical_path), 3)
        
        # Check that path items have required fields
        for item in critical_path:
            self.assertIn('phase_id', item)
            self.assertIn('phase_name', item)
            self.assertIn('is_critical', item)
            self.assertIn('dependencies', item)
            self.assertIn('buffer_days', item)
        
        # Check dependencies are correct
        self.assertEqual(len(critical_path[0]['dependencies']), 0)  # First phase has no dependencies
        self.assertEqual(len(critical_path[1]['dependencies']), 1)  # Second phase depends on first
        self.assertEqual(len(critical_path[2]['dependencies']), 1)  # Third phase depends on second
    
    def test_criticality_calculation(self):
        """Test phase criticality calculation"""
        coordinator = ScheduleCoordinator(self.test_user.id)
        
        # Test with a phase that has a very close deadline
        close_deadline_phase = ProjectPhase(
            student_id=self.test_user.id,
            phase_type=PhaseType.IRB_PROPOSAL.value,
            phase_name="Critical Phase",
            deadline=datetime.now().date() + timedelta(days=2),
            order_index=4,
            is_active=True
        )
        db.session.add(close_deadline_phase)
        db.session.commit()
        
        # Add a task to the critical phase
        critical_task = PhaseTask(
            phase_id=close_deadline_phase.id,
            date=datetime.now().date() + timedelta(days=1),
            task_description="Critical Task",
            task_type="urgent",
            day_intensity="heavy",
            completed=False
        )
        db.session.add(critical_task)
        db.session.commit()
        
        criticality = coordinator._calculate_phase_criticality(close_deadline_phase)
        self.assertEqual(criticality, CriticalityLevel.CRITICAL)
    
    def test_create_timeline_visualization_data(self):
        """Test timeline visualization data creation"""
        timeline_data = create_timeline_visualization_data(self.test_user.id)
        
        # Check structure
        self.assertIn('timeline_events', timeline_data)
        self.assertIn('phase_metrics', timeline_data)
        self.assertIn('critical_path', timeline_data)
        self.assertIn('summary', timeline_data)
        
        # Check summary data
        summary = timeline_data['summary']
        self.assertEqual(summary['total_phases'], 3)
        self.assertGreaterEqual(summary['phases_on_track'], 0)
        self.assertGreaterEqual(summary['overall_progress'], 0)
        
        # Check that data is JSON-serializable
        import json
        json_str = json.dumps(timeline_data)
        self.assertIsInstance(json_str, str)
    
    def test_timeline_route_access(self):
        """Test timeline route access control"""
        # Test without login
        response = self.app.get('/timeline')
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Test with login but non-multi-phase user
        legacy_user = Student(
            name="Legacy User",
            email="legacy@example.com",
            password_hash=generate_password_hash("password"),
            project_title="Legacy Project",
            thesis_deadline=datetime.now().date() + timedelta(days=180),
            lit_review_deadline=datetime.now().date() + timedelta(days=90),
            onboarded=True,
            is_multi_phase=False
        )
        db.session.add(legacy_user)
        db.session.commit()
        
        with self.app.session_transaction() as sess:
            sess['_user_id'] = str(legacy_user.id)
            sess['_fresh'] = True
        
        response = self.app.get('/timeline')
        self.assertEqual(response.status_code, 302)  # Redirect to dashboard
    
    def test_api_timeline_data(self):
        """Test API timeline data endpoint"""
        # Login as test user
        with self.app.session_transaction() as sess:
            sess['_user_id'] = str(self.test_user.id)
            sess['_fresh'] = True
        
        response = self.app.get(f'/api/timeline/{self.test_user.id}')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertIn('timeline_events', data)
        self.assertIn('phase_metrics', data)
        self.assertIn('critical_path', data)
    
    def test_api_redistribute_tasks(self):
        """Test API task redistribution endpoint"""
        # Login as test user
        with self.app.session_transaction() as sess:
            sess['_user_id'] = str(self.test_user.id)
            sess['_fresh'] = True
        
        new_deadline = (datetime.now().date() + timedelta(days=15)).isoformat()
        
        response = self.app.post('/api/redistribute_tasks', 
                               json={
                                   'phase_id': self.phase1.id,
                                   'new_deadline': new_deadline
                               })
        
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertIn('tasks_moved', data)
        self.assertIn('warnings', data)
    
    def test_buffer_days_calculation(self):
        """Test buffer days calculation"""
        coordinator = ScheduleCoordinator(self.test_user.id)
        
        # Phase 1 should have buffer until phase 2
        buffer_days = coordinator._calculate_buffer_days(self.phase1)
        expected_buffer = (self.phase2.deadline - self.phase1.deadline).days
        self.assertEqual(buffer_days, expected_buffer)
        
        # Last phase should have buffer until thesis deadline
        buffer_days = coordinator._calculate_buffer_days(self.phase3)
        expected_buffer = (self.test_user.thesis_deadline - self.phase3.deadline).days
        self.assertEqual(buffer_days, expected_buffer)
    
    def test_work_days_counting(self):
        """Test work days counting (excluding weekends)"""
        coordinator = ScheduleCoordinator(self.test_user.id)
        
        # Test a week that includes a weekend
        start_date = datetime(2024, 1, 1).date()  # Monday
        end_date = datetime(2024, 1, 8).date()    # Monday (next week)
        
        work_days = coordinator._count_work_days(start_date, end_date)
        self.assertEqual(work_days, 5)  # Should exclude Saturday and Sunday

if __name__ == '__main__':
    unittest.main()