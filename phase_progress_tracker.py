#!/usr/bin/env python3

"""
Phase Progress Tracker for Multi-Phase Project Management

This module provides phase-aware progress tracking, milestone detection,
and celebration features for multi-phase research projects.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json

# Import models inside functions to avoid circular imports


class MilestoneType(Enum):
    """Types of milestones that can be achieved"""
    PHASE_START = "phase_start"
    QUARTER_COMPLETE = "quarter_complete"
    HALF_COMPLETE = "half_complete"
    THREE_QUARTER_COMPLETE = "three_quarter_complete"
    PHASE_COMPLETE = "phase_complete"
    STREAK_ACHIEVEMENT = "streak_achievement"
    EARLY_COMPLETION = "early_completion"


@dataclass
class ProgressMilestone:
    """Represents a progress milestone"""
    milestone_type: MilestoneType
    phase_id: int
    phase_name: str
    achievement_date: datetime
    description: str
    celebration_message: str
    progress_percentage: float
    tasks_completed: int
    total_tasks: int


@dataclass
class PhaseProgressSummary:
    """Summary of progress for a specific phase"""
    phase_id: int
    phase_name: str
    phase_type: str
    start_date: datetime
    deadline: datetime
    total_tasks: int
    completed_tasks: int
    progress_percentage: float
    days_active: int
    days_remaining: int
    average_tasks_per_day: float
    current_streak: int
    longest_streak: int
    milestones_achieved: List[ProgressMilestone]
    is_on_track: bool
    completion_prediction: Optional[datetime]


class PhaseProgressTracker:
    """
    Tracks progress across phases with milestone detection and celebration features.
    """
    
    def __init__(self, student_id: int):
        """Initialize tracker for a specific student"""
        from app import db, Student, ProjectPhase, PhaseTask, ProgressLog
        
        self.student_id = student_id
        self.student = Student.query.get(student_id)
        if not self.student or not self.student.is_multi_phase:
            raise ValueError("Student not found or not using multi-phase system")
        
        self.phases = ProjectPhase.query.filter_by(
            student_id=student_id,
            is_active=True
        ).order_by(ProjectPhase.order_index).all()
    
    def log_phase_progress(self, phase_id: int, completed_task_ids: List[int], 
                          notes: str = "", date: datetime = None) -> Dict[str, any]:
        """
        Log progress for a specific phase and detect milestones.
        
        Args:
            phase_id: ID of the phase
            completed_task_ids: List of task IDs that were completed
            notes: Optional notes about the progress
            date: Date of progress (defaults to today)
            
        Returns:
            Dictionary with progress info and any milestones achieved
        """
        from app import db, ProjectPhase, PhaseTask, ProgressLog
        
        if date is None:
            date = datetime.now().date()
        
        # Verify phase belongs to student
        phase = ProjectPhase.query.get(phase_id)
        if not phase or phase.student_id != self.student_id:
            raise ValueError("Phase not found or access denied")
        
        # Calculate current progress
        total_tasks = PhaseTask.query.filter_by(phase_id=phase_id).count()
        completed_tasks = PhaseTask.query.filter_by(phase_id=phase_id, completed=True).count()
        progress_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # Check for milestones
        milestones = self._check_milestones(phase_id, progress_percentage, completed_tasks, total_tasks)
        
        # Create progress log entry
        progress_log = ProgressLog(
            student_id=self.student_id,
            date=date,
            tasks_completed=json.dumps([]),  # Legacy field
            notes=notes,
            phase_id=phase_id,
            phase_tasks_completed=json.dumps(completed_task_ids),
            phase_progress_percentage=progress_percentage,
            milestone_achieved=milestones[0].milestone_type.value if milestones else None
        )
        
        db.session.add(progress_log)
        db.session.commit()
        
        return {
            'progress_percentage': progress_percentage,
            'completed_tasks': completed_tasks,
            'total_tasks': total_tasks,
            'milestones_achieved': [
                {
                    'type': m.milestone_type.value,
                    'description': m.description,
                    'celebration_message': m.celebration_message,
                    'progress_percentage': m.progress_percentage
                }
                for m in milestones
            ],
            'phase_name': phase.phase_name
        }
    
    def get_phase_progress_summary(self, phase_id: int) -> PhaseProgressSummary:
        """
        Get comprehensive progress summary for a phase.
        
        Args:
            phase_id: ID of the phase
            
        Returns:
            PhaseProgressSummary object with detailed progress information
        """
        from app import db, ProjectPhase, PhaseTask, ProgressLog
        
        phase = ProjectPhase.query.get(phase_id)
        if not phase or phase.student_id != self.student_id:
            raise ValueError("Phase not found or access denied")
        
        # Get task statistics
        total_tasks = PhaseTask.query.filter_by(phase_id=phase_id).count()
        completed_tasks = PhaseTask.query.filter_by(phase_id=phase_id, completed=True).count()
        progress_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # Get progress logs for this phase
        progress_logs = ProgressLog.query.filter_by(
            student_id=self.student_id,
            phase_id=phase_id
        ).order_by(ProgressLog.date).all()
        
        # Calculate activity metrics
        today = datetime.now().date()
        start_date = progress_logs[0].date if progress_logs else today
        days_active = (today - start_date).days + 1 if progress_logs else 0
        days_remaining = (phase.deadline - today).days
        
        # Calculate streaks
        current_streak, longest_streak = self._calculate_streaks(progress_logs)
        
        # Calculate average tasks per day
        average_tasks_per_day = completed_tasks / days_active if days_active > 0 else 0
        
        # Get milestones achieved
        milestones = self._get_achieved_milestones(phase_id)
        
        # Predict completion date
        completion_prediction = self._predict_completion_date(
            phase, completed_tasks, total_tasks, average_tasks_per_day
        )
        
        # Determine if on track
        is_on_track = self._is_phase_on_track(
            progress_percentage, days_remaining, phase.deadline, start_date
        )
        
        return PhaseProgressSummary(
            phase_id=phase_id,
            phase_name=phase.phase_name,
            phase_type=phase.phase_type,
            start_date=start_date,
            deadline=phase.deadline,
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            progress_percentage=progress_percentage,
            days_active=days_active,
            days_remaining=days_remaining,
            average_tasks_per_day=average_tasks_per_day,
            current_streak=current_streak,
            longest_streak=longest_streak,
            milestones_achieved=milestones,
            is_on_track=is_on_track,
            completion_prediction=completion_prediction
        )
    
    def get_overall_progress_summary(self) -> Dict[str, any]:
        """
        Get overall progress summary across all phases.
        
        Returns:
            Dictionary with overall progress statistics
        """
        phase_summaries = []
        total_tasks = 0
        total_completed = 0
        total_milestones = 0
        phases_on_track = 0
        
        for phase in self.phases:
            summary = self.get_phase_progress_summary(phase.id)
            phase_summaries.append(summary)
            
            total_tasks += summary.total_tasks
            total_completed += summary.completed_tasks
            total_milestones += len(summary.milestones_achieved)
            
            if summary.is_on_track:
                phases_on_track += 1
        
        overall_progress = (total_completed / total_tasks * 100) if total_tasks > 0 else 0
        
        # Find most active phase (highest progress percentage)
        most_active_phase = max(phase_summaries, key=lambda p: p.progress_percentage) if phase_summaries else None
        
        # Find next milestone opportunity
        next_milestone = self._find_next_milestone_opportunity(phase_summaries)
        
        return {
            'overall_progress_percentage': overall_progress,
            'total_tasks': total_tasks,
            'total_completed': total_completed,
            'total_phases': len(self.phases),
            'phases_on_track': phases_on_track,
            'total_milestones_achieved': total_milestones,
            'most_active_phase': {
                'name': most_active_phase.phase_name,
                'progress': most_active_phase.progress_percentage
            } if most_active_phase else None,
            'next_milestone': next_milestone,
            'phase_summaries': [
                {
                    'phase_id': s.phase_id,
                    'phase_name': s.phase_name,
                    'progress_percentage': s.progress_percentage,
                    'is_on_track': s.is_on_track,
                    'days_remaining': s.days_remaining,
                    'current_streak': s.current_streak
                }
                for s in phase_summaries
            ]
        }
    
    def detect_phase_completion(self, phase_id: int) -> Optional[Dict[str, any]]:
        """
        Check if a phase has been completed and generate celebration data.
        
        Args:
            phase_id: ID of the phase to check
            
        Returns:
            Celebration data if phase is complete, None otherwise
        """
        from app import PhaseTask, ProjectPhase
        
        phase = ProjectPhase.query.get(phase_id)
        if not phase or phase.student_id != self.student_id:
            return None
        
        total_tasks = PhaseTask.query.filter_by(phase_id=phase_id).count()
        completed_tasks = PhaseTask.query.filter_by(phase_id=phase_id, completed=True).count()
        
        if total_tasks > 0 and completed_tasks == total_tasks:
            # Phase is complete!
            today = datetime.now().date()
            days_early = (phase.deadline - today).days
            
            celebration_data = {
                'phase_id': phase_id,
                'phase_name': phase.phase_name,
                'completion_date': today,
                'total_tasks': total_tasks,
                'days_early': max(0, days_early),
                'celebration_message': self._generate_completion_message(phase, days_early),
                'achievement_badges': self._generate_achievement_badges(phase_id, days_early),
                'next_phase': self._get_next_phase(phase)
            }
            
            return celebration_data
        
        return None
    
    def _check_milestones(self, phase_id: int, progress_percentage: float, 
                         completed_tasks: int, total_tasks: int) -> List[ProgressMilestone]:
        """Check for newly achieved milestones"""
        from app import ProjectPhase, ProgressLog
        
        milestones = []
        phase = ProjectPhase.query.get(phase_id)
        
        # Get previous progress to see what's new
        previous_log = ProgressLog.query.filter_by(
            student_id=self.student_id,
            phase_id=phase_id
        ).order_by(ProgressLog.date.desc()).first()
        
        previous_progress = previous_log.phase_progress_percentage if previous_log else 0
        
        # Check percentage milestones
        milestone_thresholds = [
            (25, MilestoneType.QUARTER_COMPLETE, "Quarter Complete! 🎯"),
            (50, MilestoneType.HALF_COMPLETE, "Halfway There! 🚀"),
            (75, MilestoneType.THREE_QUARTER_COMPLETE, "Three Quarters Done! 💪"),
            (100, MilestoneType.PHASE_COMPLETE, "Phase Complete! 🎉")
        ]
        
        for threshold, milestone_type, message in milestone_thresholds:
            if progress_percentage >= threshold and previous_progress < threshold:
                milestones.append(ProgressMilestone(
                    milestone_type=milestone_type,
                    phase_id=phase_id,
                    phase_name=phase.phase_name,
                    achievement_date=datetime.now(),
                    description=f"Reached {threshold}% completion in {phase.phase_name}",
                    celebration_message=message,
                    progress_percentage=progress_percentage,
                    tasks_completed=completed_tasks,
                    total_tasks=total_tasks
                ))
        
        return milestones
    
    def _calculate_streaks(self, progress_logs: List) -> Tuple[int, int]:
        """Calculate current and longest streaks from progress logs"""
        if not progress_logs:
            return 0, 0
        
        # Sort logs by date
        sorted_logs = sorted(progress_logs, key=lambda x: x.date)
        
        current_streak = 0
        longest_streak = 0
        temp_streak = 0
        
        # Calculate streaks based on consecutive days with progress
        for i, log in enumerate(sorted_logs):
            if i == 0:
                temp_streak = 1
            else:
                prev_date = sorted_logs[i-1].date
                current_date = log.date
                
                # Check if consecutive days
                if (current_date - prev_date).days == 1:
                    temp_streak += 1
                else:
                    longest_streak = max(longest_streak, temp_streak)
                    temp_streak = 1
        
        # Update longest streak with final temp_streak
        longest_streak = max(longest_streak, temp_streak)
        
        # Current streak is the most recent consecutive days
        today = datetime.now().date()
        if sorted_logs and (today - sorted_logs[-1].date).days <= 1:
            current_streak = temp_streak
        
        return current_streak, longest_streak
    
    def _get_achieved_milestones(self, phase_id: int) -> List[ProgressMilestone]:
        """Get all milestones achieved for a phase"""
        from app import ProgressLog
        
        milestone_logs = ProgressLog.query.filter_by(
            student_id=self.student_id,
            phase_id=phase_id
        ).filter(ProgressLog.milestone_achieved.isnot(None)).all()
        
        milestones = []
        for log in milestone_logs:
            try:
                milestone_type = MilestoneType(log.milestone_achieved)
                milestones.append(ProgressMilestone(
                    milestone_type=milestone_type,
                    phase_id=phase_id,
                    phase_name=log.phase.phase_name,
                    achievement_date=log.created_at,
                    description=f"Achieved {milestone_type.value}",
                    celebration_message="Milestone achieved!",
                    progress_percentage=log.phase_progress_percentage,
                    tasks_completed=0,  # Would need to calculate from JSON
                    total_tasks=0
                ))
            except ValueError:
                # Skip invalid milestone types
                continue
        
        return milestones
    
    def _predict_completion_date(self, phase, completed_tasks: int, total_tasks: int, 
                               average_tasks_per_day: float) -> Optional[datetime]:
        """Predict when phase will be completed based on current progress"""
        if average_tasks_per_day <= 0 or completed_tasks >= total_tasks:
            return None
        
        remaining_tasks = total_tasks - completed_tasks
        days_needed = remaining_tasks / average_tasks_per_day
        
        predicted_date = datetime.now().date() + timedelta(days=int(days_needed))
        return predicted_date
    
    def _is_phase_on_track(self, progress_percentage: float, days_remaining: int, 
                          deadline: datetime, start_date: datetime) -> bool:
        """Determine if phase is on track for completion"""
        if days_remaining <= 0:
            return progress_percentage >= 100
        
        # Calculate expected progress based on time elapsed
        total_days = (deadline - start_date).days
        days_elapsed = total_days - days_remaining
        expected_progress = (days_elapsed / total_days) * 100 if total_days > 0 else 0
        
        # Allow 10% tolerance
        return progress_percentage >= expected_progress * 0.9
    
    def _find_next_milestone_opportunity(self, phase_summaries: List[PhaseProgressSummary]) -> Optional[Dict[str, any]]:
        """Find the next milestone opportunity across all phases"""
        next_milestones = []
        
        for summary in phase_summaries:
            progress = summary.progress_percentage
            
            # Find next milestone threshold
            thresholds = [25, 50, 75, 100]
            for threshold in thresholds:
                if progress < threshold:
                    tasks_needed = int((threshold - progress) / 100 * summary.total_tasks)
                    next_milestones.append({
                        'phase_name': summary.phase_name,
                        'phase_id': summary.phase_id,
                        'milestone_percentage': threshold,
                        'tasks_needed': tasks_needed,
                        'current_progress': progress
                    })
                    break
        
        # Return the closest milestone
        if next_milestones:
            return min(next_milestones, key=lambda x: x['tasks_needed'])
        
        return None
    
    def _generate_completion_message(self, phase, days_early: int) -> str:
        """Generate a celebration message for phase completion"""
        base_messages = [
            f"🎉 Congratulations! You've completed the {phase.phase_name} phase!",
            f"🚀 Amazing work! The {phase.phase_name} phase is now complete!",
            f"💪 Excellent! You've successfully finished the {phase.phase_name} phase!"
        ]
        
        if days_early > 0:
            early_messages = [
                f"And you finished {days_early} days early! Outstanding time management! ⏰",
                f"Plus, you're {days_early} days ahead of schedule! Incredible efficiency! 📈",
                f"You completed this {days_early} days before the deadline! Superb planning! 🎯"
            ]
            return f"{base_messages[0]} {early_messages[0]}"
        
        return base_messages[0]
    
    def _generate_achievement_badges(self, phase_id: int, days_early: int) -> List[str]:
        """Generate achievement badges for phase completion"""
        badges = ["Phase Completed 🏆"]
        
        if days_early > 0:
            badges.append("Early Bird 🐦")
        
        if days_early >= 7:
            badges.append("Time Master ⏰")
        
        # Add streak-based badges
        summary = self.get_phase_progress_summary(phase_id)
        if summary.longest_streak >= 7:
            badges.append("Consistency Champion 🔥")
        
        if summary.longest_streak >= 14:
            badges.append("Dedication Master 💎")
        
        return badges
    
    def _get_next_phase(self, current_phase) -> Optional[Dict[str, any]]:
        """Get information about the next phase"""
        next_phases = [p for p in self.phases if p.order_index > current_phase.order_index]
        
        if next_phases:
            next_phase = min(next_phases, key=lambda p: p.order_index)
            return {
                'phase_id': next_phase.id,
                'phase_name': next_phase.phase_name,
                'deadline': next_phase.deadline.isoformat(),
                'days_until_start': 1  # Could be calculated based on dependencies
            }
        
        return None


def create_progress_visualization_data(student_id: int) -> Dict[str, any]:
    """
    Create data structure for progress visualization in the frontend.
    
    Args:
        student_id: ID of the student
        
    Returns:
        Dictionary with progress visualization data
    """
    tracker = PhaseProgressTracker(student_id)
    overall_summary = tracker.get_overall_progress_summary()
    
    # Get detailed summaries for each phase
    detailed_summaries = []
    for phase in tracker.phases:
        summary = tracker.get_phase_progress_summary(phase.id)
        detailed_summaries.append({
            'phase_id': summary.phase_id,
            'phase_name': summary.phase_name,
            'phase_type': summary.phase_type,
            'progress_percentage': summary.progress_percentage,
            'completed_tasks': summary.completed_tasks,
            'total_tasks': summary.total_tasks,
            'days_remaining': summary.days_remaining,
            'current_streak': summary.current_streak,
            'longest_streak': summary.longest_streak,
            'is_on_track': summary.is_on_track,
            'milestones_achieved': [
                {
                    'type': m.milestone_type.value,
                    'description': m.description,
                    'achievement_date': m.achievement_date.isoformat(),
                    'celebration_message': m.celebration_message
                }
                for m in summary.milestones_achieved
            ],
            'completion_prediction': summary.completion_prediction.isoformat() if summary.completion_prediction else None
        })
    
    return {
        'overall_summary': overall_summary,
        'phase_details': detailed_summaries,
        'student_id': student_id
    }