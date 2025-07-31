#!/usr/bin/env python3

"""
Schedule Coordinator for Multi-Phase Project Management

This module provides cross-phase timeline management, automatic task redistribution,
and critical path analysis for multi-phase research projects.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# Import models inside functions to avoid circular imports


class CriticalityLevel(Enum):
    """Criticality levels for timeline analysis"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class TimelineEvent:
    """Represents an event in the project timeline"""
    date: datetime
    event_type: str  # 'deadline', 'milestone', 'task_cluster'
    phase_id: int
    phase_name: str
    description: str
    criticality: CriticalityLevel
    buffer_days: int = 0


@dataclass
class PhaseMetrics:
    """Metrics for a single phase"""
    phase_id: int
    phase_name: str
    start_date: datetime
    deadline: datetime
    total_tasks: int
    completed_tasks: int
    remaining_tasks: int
    progress_percentage: float
    days_remaining: int
    tasks_per_day_required: float
    criticality: CriticalityLevel
    is_on_track: bool
    buffer_days: int


class ScheduleCoordinator:
    """
    Coordinates scheduling across multiple phases of a research project.
    
    Provides timeline management, automatic task redistribution, and critical path analysis.
    """
    
    def __init__(self, student_id: int):
        """Initialize coordinator for a specific student"""
        from flask import current_app
        from app import Student, ProjectPhase
        
        self.student_id = student_id
        db = current_app.extensions['sqlalchemy'].db
        
        self.student = db.session.query(Student).get(student_id)
        if not self.student or not self.student.is_multi_phase:
            raise ValueError("Student not found or not using multi-phase system")
        
        self.phases = db.session.query(ProjectPhase).filter_by(
            student_id=student_id,
            is_active=True
        ).order_by(ProjectPhase.order_index).all()
    
    def get_integrated_timeline(self) -> List[TimelineEvent]:
        """
        Generate an integrated timeline showing all phases and their key events.
        
        Returns:
            List of TimelineEvent objects sorted by date
        """
        events = []
        today = datetime.now().date()
        
        for phase in self.phases:
            # Add phase deadline as major event
            criticality = self._calculate_phase_criticality(phase)
            
            events.append(TimelineEvent(
                date=phase.deadline,
                event_type='deadline',
                phase_id=phase.id,
                phase_name=phase.phase_name,
                description=f"{phase.phase_name} deadline",
                criticality=criticality,
                buffer_days=self._calculate_buffer_days(phase)
            ))
            
            # Add task clusters (groups of tasks on same day)
            task_clusters = self._get_task_clusters(phase)
            for date, task_count in task_clusters.items():
                if date >= today:  # Only future events
                    events.append(TimelineEvent(
                        date=date,
                        event_type='task_cluster',
                        phase_id=phase.id,
                        phase_name=phase.phase_name,
                        description=f"{task_count} tasks scheduled",
                        criticality=CriticalityLevel.LOW if task_count <= 2 else CriticalityLevel.MEDIUM,
                        buffer_days=0
                    ))
        
        # Sort events by date
        events.sort(key=lambda x: x.date)
        return events
    
    def get_phase_metrics(self) -> List[PhaseMetrics]:
        """
        Calculate comprehensive metrics for all phases.
        
        Returns:
            List of PhaseMetrics objects
        """
        metrics = []
        today = datetime.now().date()
        
        for phase in self.phases:
            from app import PhaseTask
            tasks = PhaseTask.query.filter_by(phase_id=phase.id).all()
            
            total_tasks = len(tasks)
            completed_tasks = len([t for t in tasks if t.completed])
            remaining_tasks = total_tasks - completed_tasks
            
            progress_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            days_remaining = (phase.deadline - today).days
            
            # Calculate required tasks per day
            tasks_per_day_required = 0
            if days_remaining > 0 and remaining_tasks > 0:
                # Only count work days (exclude weekends)
                work_days = self._count_work_days(today, phase.deadline)
                tasks_per_day_required = remaining_tasks / work_days if work_days > 0 else float('inf')
            
            # Determine criticality
            criticality = self._calculate_phase_criticality(phase)
            
            # Check if on track
            is_on_track = self._is_phase_on_track(phase, progress_percentage, days_remaining)
            
            # Calculate buffer days
            buffer_days = self._calculate_buffer_days(phase)
            
            # Estimate start date based on previous phases
            start_date = self._estimate_phase_start_date(phase)
            
            metrics.append(PhaseMetrics(
                phase_id=phase.id,
                phase_name=phase.phase_name,
                start_date=start_date,
                deadline=phase.deadline,
                total_tasks=total_tasks,
                completed_tasks=completed_tasks,
                remaining_tasks=remaining_tasks,
                progress_percentage=progress_percentage,
                days_remaining=days_remaining,
                tasks_per_day_required=tasks_per_day_required,
                criticality=criticality,
                is_on_track=is_on_track,
                buffer_days=buffer_days
            ))
        
        return metrics
    
    def redistribute_tasks_after_deadline_change(self, phase_id: int, new_deadline: datetime) -> Dict[str, any]:
        """
        Automatically redistribute tasks when a phase deadline changes.
        
        Args:
            phase_id: ID of the phase with changed deadline
            new_deadline: New deadline for the phase
            
        Returns:
            Dictionary with redistribution results and warnings
        """
        from app import db, ProjectPhase, PhaseTask
        
        phase = ProjectPhase.query.get(phase_id)
        if not phase or phase.student_id != self.student_id:
            raise ValueError("Phase not found or access denied")
        
        old_deadline = phase.deadline
        phase.deadline = new_deadline
        
        # Get all incomplete tasks for this phase
        incomplete_tasks = PhaseTask.query.filter_by(
            phase_id=phase_id,
            completed=False
        ).order_by(PhaseTask.date).all()
        
        if not incomplete_tasks:
            db.session.commit()
            return {
                'success': True,
                'message': 'Deadline updated successfully. No tasks to redistribute.',
                'tasks_moved': 0,
                'warnings': []
            }
        
        # Calculate new distribution
        today = datetime.now().date()
        available_days = self._get_available_work_days(today, new_deadline)
        
        warnings = []
        tasks_moved = 0
        
        if len(incomplete_tasks) > len(available_days):
            warnings.append(f"Not enough work days ({len(available_days)}) for all tasks ({len(incomplete_tasks)})")
        
        # Redistribute tasks across available days
        for i, task in enumerate(incomplete_tasks):
            if i < len(available_days):
                old_date = task.date
                task.date = available_days[i]
                if old_date != task.date:
                    tasks_moved += 1
            else:
                # If we run out of days, stack tasks on the last available day
                task.date = available_days[-1] if available_days else new_deadline
                tasks_moved += 1
                warnings.append(f"Task '{task.task_description}' scheduled on deadline day due to time constraints")
        
        # Check for conflicts with other phases
        conflicts = self._check_phase_conflicts(phase_id, new_deadline)
        warnings.extend(conflicts)
        
        try:
            db.session.commit()
            return {
                'success': True,
                'message': f'Deadline updated and {tasks_moved} tasks redistributed.',
                'tasks_moved': tasks_moved,
                'warnings': warnings
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Error updating deadline: {str(e)}',
                'tasks_moved': 0,
                'warnings': warnings
            }
    
    def get_critical_path(self) -> List[Dict[str, any]]:
        """
        Identify the critical path through all phases.
        
        Returns:
            List of critical path elements with timing and dependencies
        """
        critical_path = []
        
        for i, phase in enumerate(self.phases):
            metrics = self.get_phase_metrics()
            phase_metric = next((m for m in metrics if m.phase_id == phase.id), None)
            
            if not phase_metric:
                continue
            
            # Determine if this phase is on the critical path
            is_critical = (
                phase_metric.criticality in [CriticalityLevel.HIGH, CriticalityLevel.CRITICAL] or
                phase_metric.buffer_days < 7 or
                not phase_metric.is_on_track
            )
            
            # Calculate dependencies
            dependencies = []
            if i > 0:
                prev_phase = self.phases[i-1]
                dependencies.append({
                    'phase_id': prev_phase.id,
                    'phase_name': prev_phase.phase_name,
                    'relationship': 'prerequisite'
                })
            
            critical_path.append({
                'phase_id': phase.id,
                'phase_name': phase.phase_name,
                'start_date': phase_metric.start_date.isoformat() if hasattr(phase_metric.start_date, 'isoformat') else str(phase_metric.start_date),
                'deadline': phase_metric.deadline.isoformat() if hasattr(phase_metric.deadline, 'isoformat') else str(phase_metric.deadline),
                'duration_days': (phase_metric.deadline - phase_metric.start_date).days,
                'buffer_days': phase_metric.buffer_days,
                'is_critical': is_critical,
                'criticality_reason': self._get_criticality_reason(phase_metric),
                'dependencies': dependencies,
                'progress_percentage': phase_metric.progress_percentage,
                'tasks_remaining': phase_metric.remaining_tasks
            })
        
        return critical_path
    
    def _calculate_phase_criticality(self, phase) -> CriticalityLevel:
        """Calculate criticality level for a phase"""
        from flask import current_app
        from app import PhaseTask
        
        today = datetime.now().date()
        days_remaining = (phase.deadline - today).days
        
        db = current_app.extensions['sqlalchemy'].db
        tasks = db.session.query(PhaseTask).filter_by(phase_id=phase.id).all()
        if not tasks:
            return CriticalityLevel.LOW
        
        completed_tasks = len([t for t in tasks if t.completed])
        progress_percentage = (completed_tasks / len(tasks)) * 100
        
        # Critical if deadline is very close
        if days_remaining <= 3:
            return CriticalityLevel.CRITICAL
        elif days_remaining <= 7:
            return CriticalityLevel.HIGH
        
        # Critical if far behind schedule
        expected_progress = max(0, 100 - (days_remaining / 30 * 100))  # Rough estimate
        if progress_percentage < expected_progress - 30:
            return CriticalityLevel.CRITICAL
        elif progress_percentage < expected_progress - 15:
            return CriticalityLevel.HIGH
        elif progress_percentage < expected_progress:
            return CriticalityLevel.MEDIUM
        
        return CriticalityLevel.LOW
    
    def _calculate_buffer_days(self, phase) -> int:
        """Calculate buffer days available for a phase"""
        today = datetime.now().date()
        
        # Find the next phase deadline
        next_phases = [p for p in self.phases if p.order_index > phase.order_index]
        if next_phases:
            next_deadline = min(p.deadline for p in next_phases)
            buffer_days = (next_deadline - phase.deadline).days
        else:
            # Use thesis deadline as final buffer
            if self.student.thesis_deadline:
                buffer_days = (self.student.thesis_deadline - phase.deadline).days
            else:
                buffer_days = 0
        
        return max(0, buffer_days)
    
    def _get_task_clusters(self, phase) -> Dict[datetime, int]:
        """Get task clusters (multiple tasks on same day) for a phase"""
        from flask import current_app
        from app import PhaseTask
        
        db = current_app.extensions['sqlalchemy'].db
        tasks = db.session.query(PhaseTask).filter_by(phase_id=phase.id).all()
        clusters = {}
        
        for task in tasks:
            if task.date in clusters:
                clusters[task.date] += 1
            else:
                clusters[task.date] = 1
        
        # Only return days with multiple tasks
        return {date: count for date, count in clusters.items() if count > 1}
    
    def _count_work_days(self, start_date: datetime, end_date: datetime) -> int:
        """Count work days between two dates (excluding weekends)"""
        current = start_date
        work_days = 0
        
        while current < end_date:
            if current.weekday() < 5:  # Monday = 0, Friday = 4
                work_days += 1
            current += timedelta(days=1)
        
        return work_days
    
    def _is_phase_on_track(self, phase, progress_percentage: float, days_remaining: int) -> bool:
        """Determine if a phase is on track to meet its deadline"""
        if days_remaining <= 0:
            return progress_percentage >= 100
        
        # Simple heuristic: should be at least 50% done when 50% of time has passed
        total_days = (phase.deadline - phase.created_at.date()).days if hasattr(phase, 'created_at') else 30
        days_elapsed = total_days - days_remaining
        expected_progress = (days_elapsed / total_days) * 100 if total_days > 0 else 0
        
        return progress_percentage >= expected_progress * 0.8  # Allow 20% tolerance
    
    def _estimate_phase_start_date(self, phase) -> datetime:
        """Estimate when a phase should start based on dependencies"""
        # For now, use a simple approach based on order
        if phase.order_index == 1:
            return datetime.now().date()
        
        # Find previous phase
        prev_phases = [p for p in self.phases if p.order_index < phase.order_index]
        if prev_phases:
            latest_prev_deadline = max(p.deadline for p in prev_phases)
            return latest_prev_deadline + timedelta(days=1)
        
        return datetime.now().date()
    
    def _get_available_work_days(self, start_date: datetime, end_date: datetime) -> List[datetime]:
        """Get list of available work days between two dates"""
        work_days = []
        current = start_date
        
        while current <= end_date:
            if current.weekday() < 5:  # Monday to Friday
                work_days.append(current)
            current += timedelta(days=1)
        
        return work_days
    
    def _check_phase_conflicts(self, phase_id: int, new_deadline: datetime) -> List[str]:
        """Check for conflicts with other phases when deadline changes"""
        warnings = []
        
        # Check if new deadline conflicts with subsequent phases
        from app import ProjectPhase
        
        phase = ProjectPhase.query.get(phase_id)
        subsequent_phases = [p for p in self.phases if p.order_index > phase.order_index]
        
        for subsequent_phase in subsequent_phases:
            if new_deadline >= subsequent_phase.deadline:
                warnings.append(
                    f"New deadline conflicts with {subsequent_phase.phase_name} "
                    f"(due {subsequent_phase.deadline.strftime('%Y-%m-%d')})"
                )
        
        return warnings
    
    def _get_criticality_reason(self, metrics: PhaseMetrics) -> str:
        """Get human-readable reason for phase criticality"""
        if metrics.days_remaining <= 3:
            return "Deadline is within 3 days"
        elif metrics.days_remaining <= 7:
            return "Deadline is within 1 week"
        elif not metrics.is_on_track:
            return "Behind schedule based on progress"
        elif metrics.buffer_days < 7:
            return "Limited buffer time before next phase"
        elif metrics.tasks_per_day_required > 3:
            return "High task density required"
        else:
            return "On track"


def create_timeline_visualization_data(student_id: int) -> Dict[str, any]:
    """
    Create data structure for timeline visualization in the frontend.
    
    Args:
        student_id: ID of the student
        
    Returns:
        Dictionary with timeline data for visualization
    """
    coordinator = ScheduleCoordinator(student_id)
    
    timeline_events = coordinator.get_integrated_timeline()
    phase_metrics = coordinator.get_phase_metrics()
    critical_path = coordinator.get_critical_path()
    
    return {
        'timeline_events': [
            {
                'date': event.date.isoformat() if hasattr(event.date, 'isoformat') else str(event.date),
                'event_type': event.event_type,
                'phase_id': event.phase_id,
                'phase_name': event.phase_name,
                'description': event.description,
                'criticality': event.criticality.value,
                'buffer_days': event.buffer_days
            }
            for event in timeline_events
        ],
        'phase_metrics': [
            {
                'phase_id': metric.phase_id,
                'phase_name': metric.phase_name,
                'start_date': metric.start_date.isoformat() if hasattr(metric.start_date, 'isoformat') else str(metric.start_date),
                'deadline': metric.deadline.isoformat() if hasattr(metric.deadline, 'isoformat') else str(metric.deadline),
                'progress_percentage': metric.progress_percentage,
                'days_remaining': metric.days_remaining,
                'tasks_per_day_required': metric.tasks_per_day_required,
                'criticality': metric.criticality.value,
                'is_on_track': metric.is_on_track,
                'buffer_days': metric.buffer_days,
                'total_tasks': metric.total_tasks,
                'completed_tasks': metric.completed_tasks,
                'remaining_tasks': metric.remaining_tasks
            }
            for metric in phase_metrics
        ],
        'critical_path': critical_path,
        'summary': {
            'total_phases': len(phase_metrics),
            'phases_on_track': len([m for m in phase_metrics if m.is_on_track]),
            'critical_phases': len([m for m in phase_metrics if m.criticality in [CriticalityLevel.HIGH, CriticalityLevel.CRITICAL]]),
            'total_buffer_days': sum(m.buffer_days for m in phase_metrics),
            'overall_progress': sum(m.progress_percentage for m in phase_metrics) / len(phase_metrics) if phase_metrics else 0
        }
    }
