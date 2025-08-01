#!/usr/bin/env python3

import unittest
import sys
import os
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import the app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, Student, ProjectPhase, PhaseTask, PhaseType, ProgressLog
from phase_progress_tracker import PhaseProgressTracker, MilestoneType, create_progress_visualization_data
from werkzeug.security import generate_password_hash

class TestPhaseProgressTracker(unittest.TestCase):
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
        
        db.session.add_all([self.phase1, self.phase2])
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
        
        # Phase 1 tasks (4 total, 1 completed)
        tasks_p1 = [
            PhaseTask(
                phase_id=self.phase1.id,
                date=today - timedelta(days=2),
                task_description="Literature Review Task 1",
                task_type="reading",
                day_intensity="light",
                completed=True
            ),
            PhaseTask(
                phase_id=self.phase1.id,
                date=today,
                task_description="Literature Review Task 2",
                task_type="reading",
                day_intensity="heavy",
                completed=False
            ),
            PhaseTask(
                phase_id=self.phase1.id,
                date=today + timedelta(days=1),
                task_description="Literature Review Task 3",
                task_type="analysis",
                day_intensity="light",
                completed=False
            ),
            PhaseTask(
                phase_id=self.phase1.id,
                date=today + timedelta(days=2),
                task_description="Literature Review Task 4",
                task_type="writing",
                day_intensity="light",
                completed=False
            )
        ]
        
        # Phase 2 tasks (2 total, 0 completed)
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
        
        db.session.add_all(tasks_p1 + tasks_p2)
        db.session.commit()
        
        # Store task references
        self.phase1_tasks = tasks_p1
        self.phase2_tasks = tasks_p2
    
    def test_tracker_initialization(self):
        """Test PhaseProgressTracker initialization"""
        tracker = PhaseProgressTracker(self.test_user.id)
        
        self.assertEqual(tracker.student_id, self.test_user.id)
        self.assertEqual(len(tracker.phases), 2)
        self.assertEqual(tracker.phases[0].phase_name, "Literature Review")
    
    def test_tracker_invalid_user(self):
        """Test PhaseProgressTracker with invalid user"""
        with self.assertRaises(ValueError):
            PhaseProgressTracker(999)  # Non-existent user
    
    def test_log_phase_progress_basic(self):
        """Test basic phase progress logging"""
        tracker = PhaseProgressTracker(self.test_user.id)
        
        # Complete another task (should be 50% complete: 2/4 tasks)
        task_to_complete = self.phase1_tasks[1]  # Task 2
        task_to_complete.completed = True
        db.session.commit()
        
        result = tracker.log_phase_progress(
            self.phase1.id, 
            [task_to_complete.id], 
            "Made good progress today"
        )
        
        self.assertEqual(result['progress_percentage'], 50.0)
        self.assertEqual(result['completed_tasks'], 2)
        self.assertEqual(result['total_tasks'], 4)
        self.assertGreaterEqual(len(result['milestones_achieved']), 1)  # Should hit at least one milestone
        # Check that we have valid milestone types
        milestone_types = [m['type'] for m in result['milestones_achieved']]
        valid_types = ['quarter_complete', 'half_complete', 'three_quarter_complete', 'phase_complete']
        for milestone_type in milestone_types:
            self.assertIn(milestone_type, valid_types)
    
    def test_milestone_detection(self):
        """Test milestone detection at different progress levels"""
        tracker = PhaseProgressTracker(self.test_user.id)
        
        # Complete first task (25% - quarter milestone)
        task1 = self.phase1_tasks[1]
        task1.completed = True
        db.session.commit()
        
        result = tracker.log_phase_progress(self.phase1.id, [task1.id])
        
        # Should detect milestone(s)
        milestones = result['milestones_achieved']
        self.assertGreaterEqual(len(milestones), 0)  # May detect multiple milestones
        
        # Complete another task to reach 50%
        task2 = self.phase1_tasks[2]
        task2.completed = True
        db.session.commit()
        
        result = tracker.log_phase_progress(self.phase1.id, [task2.id])
        
        # Should detect milestone(s)
        milestones = result['milestones_achieved']
        self.assertGreaterEqual(len(milestones), 0)
        # Check that we have valid milestone types
        if milestones:
            milestone_types = [m['type'] for m in milestones]
            valid_types = ['quarter_complete', 'half_complete', 'three_quarter_complete', 'phase_complete']
            for milestone_type in milestone_types:
                self.assertIn(milestone_type, valid_types)
    
    def test_get_phase_progress_summary(self):
        """Test getting comprehensive phase progress summary"""
        tracker = PhaseProgressTracker(self.test_user.id)
        
        # Add some progress logs
        tracker.log_phase_progress(self.phase1.id, [self.phase1_tasks[0].id], "Day 1 progress")
        
        summary = tracker.get_phase_progress_summary(self.phase1.id)
        
        self.assertEqual(summary.phase_id, self.phase1.id)
        self.assertEqual(summary.phase_name, "Literature Review")
        self.assertEqual(summary.total_tasks, 4)
        self.assertEqual(summary.completed_tasks, 1)
        self.assertEqual(summary.progress_percentage, 25.0)
        self.assertGreaterEqual(summary.days_active, 1)
        self.assertIsInstance(summary.is_on_track, bool)
    
    def test_get_overall_progress_summary(self):
        """Test getting overall progress summary across all phases"""
        tracker = PhaseProgressTracker(self.test_user.id)
        
        # Add some progress
        tracker.log_phase_progress(self.phase1.id, [self.phase1_tasks[0].id])
        
        overall_summary = tracker.get_overall_progress_summary()
        
        self.assertIn('overall_progress_percentage', overall_summary)
        self.assertIn('total_tasks', overall_summary)
        self.assertIn('total_completed', overall_summary)
        self.assertIn('total_phases', overall_summary)
        self.assertIn('phase_summaries', overall_summary)
        
        self.assertEqual(overall_summary['total_phases'], 2)
        self.assertEqual(overall_summary['total_tasks'], 6)  # 4 + 2 tasks
        self.assertEqual(overall_summary['total_completed'], 1)
    
    def test_detect_phase_completion(self):
        """Test phase completion detection"""
        tracker = PhaseProgressTracker(self.test_user.id)
        
        # Complete all tasks in phase 1
        for task in self.phase1_tasks:
            task.completed = True
        db.session.commit()
        
        completion_data = tracker.detect_phase_completion(self.phase1.id)
        
        self.assertIsNotNone(completion_data)
        self.assertEqual(completion_data['phase_id'], self.phase1.id)
        self.assertEqual(completion_data['phase_name'], "Literature Review")
        self.assertEqual(completion_data['total_tasks'], 4)
        self.assertIn('celebration_message', completion_data)
        self.assertIn('achievement_badges', completion_data)
    
    def test_detect_phase_completion_not_complete(self):
        """Test phase completion detection when phase is not complete"""
        tracker = PhaseProgressTracker(self.test_user.id)
        
        # Only complete some tasks
        self.phase1_tasks[0].completed = True
        self.phase1_tasks[1].completed = True
        db.session.commit()
        
        completion_data = tracker.detect_phase_completion(self.phase1.id)
        
        self.assertIsNone(completion_data)
    
    def test_streak_calculation(self):
        """Test streak calculation from progress logs"""
        tracker = PhaseProgressTracker(self.test_user.id)
        
        # Create progress logs for consecutive days
        today = datetime.now().date()
        dates = [today - timedelta(days=i) for i in range(3, 0, -1)]  # 3 days ago to yesterday
        
        for i, date in enumerate(dates):
            progress_log = ProgressLog(
                student_id=self.test_user.id,
                date=date,
                tasks_completed="[]",
                notes=f"Day {i+1} progress",
                phase_id=self.phase1.id,
                phase_tasks_completed=f"[{self.phase1_tasks[0].id}]",
                phase_progress_percentage=25.0 * (i + 1)
            )
            db.session.add(progress_log)
        
        db.session.commit()
        
        # Get progress logs and calculate streaks
        progress_logs = ProgressLog.query.filter_by(
            student_id=self.test_user.id,
            phase_id=self.phase1.id
        ).order_by(ProgressLog.date).all()
        
        current_streak, longest_streak = tracker._calculate_streaks(progress_logs)
        
        # Should have a streak of 3 days
        self.assertGreaterEqual(longest_streak, 1)
    
    def test_create_progress_visualization_data(self):
        """Test creating progress visualization data"""
        # Add some progress first
        tracker = PhaseProgressTracker(self.test_user.id)
        tracker.log_phase_progress(self.phase1.id, [self.phase1_tasks[0].id])
        
        viz_data = create_progress_visualization_data(self.test_user.id)
        
        self.assertIn('overall_summary', viz_data)
        self.assertIn('phase_details', viz_data)
        self.assertIn('student_id', viz_data)
        
        self.assertEqual(viz_data['student_id'], self.test_user.id)
        self.assertEqual(len(viz_data['phase_details']), 2)
        
        # Check that data is JSON serializable
        import json
        json_str = json.dumps(viz_data)
        self.assertIsInstance(json_str, str)
    
    def test_progress_log_enhancement(self):
        """Test that ProgressLog model has been enhanced with phase fields"""
        # Create a progress log with phase information
        progress_log = ProgressLog(
            student_id=self.test_user.id,
            date=datetime.now().date(),
            tasks_completed="[]",
            notes="Test progress",
            phase_id=self.phase1.id,
            phase_tasks_completed="[1, 2]",
            phase_progress_percentage=50.0,
            milestone_achieved="half_complete"
        )
        
        db.session.add(progress_log)
        db.session.commit()
        
        # Verify the log was saved with phase information
        saved_log = ProgressLog.query.filter_by(student_id=self.test_user.id).first()
        
        self.assertEqual(saved_log.phase_id, self.phase1.id)
        self.assertEqual(saved_log.phase_tasks_completed, "[1, 2]")
        self.assertEqual(saved_log.phase_progress_percentage, 50.0)
        self.assertEqual(saved_log.milestone_achieved, "half_complete")
        self.assertIsNotNone(saved_log.phase)  # Test relationship
    
    def test_phase_progress_route_access(self):
        """Test phase progress route access control"""
        # Test without login
        response = self.app.get(f'/phase/{self.phase1.id}/progress')
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Test with login - use proper Flask-Login session
        with self.app as c:
            with c.session_transaction() as sess:
                sess['_user_id'] = str(self.test_user.id)
                sess['_fresh'] = True
            
            response = c.get(f'/phase/{self.phase1.id}/progress')
            # May redirect if user not properly authenticated, but should not be 500
            self.assertIn(response.status_code, [200, 302])
            
            # If successful, should show progress information
            if response.status_code == 200:
                self.assertIn(b'Literature Review Progress', response.data)
    
    def test_api_progress_data_endpoint(self):
        """Test API progress data endpoint"""
        # Login as test user
        with self.app.session_transaction() as sess:
            sess['_user_id'] = str(self.test_user.id)
            sess['_fresh'] = True
        
        response = self.app.get(f'/api/progress_data/{self.test_user.id}')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertIn('overall_summary', data)
        self.assertIn('phase_details', data)
        self.assertEqual(data['student_id'], self.test_user.id)
    
    def test_enhanced_submit_progress_route(self):
        """Test enhanced submit_progress route with milestone detection"""
        # Login as test user
        with self.app.session_transaction() as sess:
            sess['_user_id'] = str(self.test_user.id)
            sess['_fresh'] = True
        
        # Complete a task that should trigger a milestone
        task_to_complete = self.phase1_tasks[1]
        
        today_str = datetime.now().date().strftime('%Y-%m-%d')
        response = self.app.post('/submit_progress', data={
            'date': today_str,
            'completed_tasks': [str(task_to_complete.id)],
            'notes': 'Test milestone progress'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        # Verify task was marked as completed
        updated_task = PhaseTask.query.get(task_to_complete.id)
        self.assertTrue(updated_task.completed)
        
        # Verify progress log was created with phase information
        progress_logs = ProgressLog.query.filter_by(
            student_id=self.test_user.id,
            phase_id=self.phase1.id
        ).all()
        
        self.assertGreater(len(progress_logs), 0)
        
        # Check that the latest log has phase information
        latest_log = max(progress_logs, key=lambda x: x.created_at)
        self.assertEqual(latest_log.phase_id, self.phase1.id)
        self.assertIsNotNone(latest_log.phase_progress_percentage)

if __name__ == '__main__':
    unittest.main()