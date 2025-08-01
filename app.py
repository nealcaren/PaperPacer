from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import json
import secrets
import os
from schedule_coordinator import ScheduleCoordinator, create_timeline_visualization_data
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import enum

# Import configuration
from config import config

app = Flask(__name__)

# Load configuration based on environment
config_name = os.environ.get('FLASK_ENV') or 'default'
app.config.from_object(config[config_name])

# Create SQLAlchemy instance after configuring app
db = SQLAlchemy()
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# Add custom Jinja filter for JSON parsing
@app.template_filter('from_json')
def from_json_filter(json_str):
    if json_str:
        return json.loads(json_str)
    return []

def send_email(to_email, subject, body_text, body_html=None):
    """Send an email using SMTP configuration"""
    if not app.config.get('MAIL_ENABLED', False):
        print(f"Email sending disabled. Would have sent to {to_email}: {subject}")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = app.config['MAIL_DEFAULT_SENDER']
        msg['To'] = to_email
        
        # Add text part
        text_part = MIMEText(body_text, 'plain')
        msg.attach(text_part)
        
        # Add HTML part if provided
        if body_html:
            html_part = MIMEText(body_html, 'html')
            msg.attach(html_part)
        
        # Send email
        server = smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT'])
        server.starttls()
        server.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        
        server.send_message(msg)
        server.quit()
        
        print(f"Email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        print(f"Failed to send email to {to_email}: {str(e)}")
        return False

# Database Models
class Student(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    project_title = db.Column(db.String(200))
    thesis_deadline = db.Column(db.Date)
    lit_review_deadline = db.Column(db.Date)
    work_days = db.Column(db.String(500))  # JSON string of day preferences with intensity
    onboarded = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Password reset fields
    reset_token = db.Column(db.String(100), nullable=True)
    reset_token_expires = db.Column(db.DateTime, nullable=True)
    
    # Multi-phase system flag
    is_multi_phase = db.Column(db.Boolean, default=False)  # Migration flag
    
    # Relationships
    schedule_items = db.relationship('ScheduleItem', backref='student', lazy=True)
    progress_logs = db.relationship('ProgressLog', backref='student', lazy=True)
    project_phases = db.relationship('ProjectPhase', backref='student', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def generate_reset_token(self):
        self.reset_token = secrets.token_urlsafe(32)
        self.reset_token_expires = datetime.utcnow() + timedelta(hours=1)  # Token expires in 1 hour
        return self.reset_token
    
    def verify_reset_token(self, token):
        if not self.reset_token or not self.reset_token_expires:
            return False
        if self.reset_token != token:
            return False
        if datetime.utcnow() > self.reset_token_expires:
            return False
        return True
    
    def clear_reset_token(self):
        self.reset_token = None
        self.reset_token_expires = None

class ScheduleItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    task_description = db.Column(db.Text, nullable=False)
    day_intensity = db.Column(db.String(20), default='light')  # 'none', 'light', 'heavy'
    priority = db.Column(db.String(10), default='medium')  # 'high', 'medium', 'low'
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ProgressLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    tasks_completed = db.Column(db.Text)  # JSON string of completed tasks
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Phase-specific progress tracking
    phase_id = db.Column(db.Integer, db.ForeignKey('project_phase.id'), nullable=True)  # Null for legacy entries
    phase_tasks_completed = db.Column(db.Text)  # JSON string of phase-specific completed tasks
    phase_progress_percentage = db.Column(db.Float, default=0.0)  # Progress percentage for the phase
    milestone_achieved = db.Column(db.String(100))  # Optional milestone name if achieved
    
    # Relationship to phase
    phase = db.relationship('ProjectPhase', backref='progress_logs')

# Phase Type Enumeration
class PhaseType(enum.Enum):
    LITERATURE_REVIEW = "literature_review"
    RESEARCH_QUESTION = "research_question"
    METHODS_PLANNING = "methods_planning"
    IRB_PROPOSAL = "irb_proposal"
    # Future phases can be added here
    DATA_COLLECTION = "data_collection"
    DATA_ANALYSIS = "data_analysis"
    WRITING = "writing"

class ProjectPhase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    phase_type = db.Column(db.String(50), nullable=False)  # 'literature_review', 'research_question', etc.
    phase_name = db.Column(db.String(100), nullable=False)  # Display name
    deadline = db.Column(db.Date, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    order_index = db.Column(db.Integer, default=0)  # For phase ordering
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    phase_tasks = db.relationship('PhaseTask', backref='project_phase', lazy=True, cascade='all, delete-orphan')

class PhaseTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phase_id = db.Column(db.Integer, db.ForeignKey('project_phase.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    task_description = db.Column(db.Text, nullable=False)
    task_type = db.Column(db.String(50), default='general')  # 'reading', 'writing', 'research', etc.
    day_intensity = db.Column(db.String(20), default='light')
    priority = db.Column(db.String(10), default='medium')  # 'high', 'medium', 'low'
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Computed property for student_id (for backward compatibility)
    @property
    def student_id(self):
        return self.project_phase.student_id

# Phase Configuration System
PHASE_TEMPLATES = {
    'literature_review': {
        'name': 'Literature Review',
        'description': 'Systematic literature search, reading, and synthesis',
        'icon': '📚',
        'default_duration_weeks': 4,
        'task_types': ['reading', 'note_taking', 'synthesis'],
        'task_templates': [
            "Create comprehensive list of initial sources from adviser recommendations",
            "Set up note-taking system with template for articles",
            "Begin wide reading to orient toward topic",
            "Start populating reading queue using citation strategies",
            "Begin thesis journal for daily progress and reflections",
            "Skim and take detailed notes on 2 articles per day",
            "Identify research questions and motivations in readings",
            "Begin identifying 2-3 major theoretical frameworks",
            "Organize sources by theme/topic (not chronologically)",
            "Meet with adviser to discuss promising directions",
            "Continue skimming 2 articles per day",
            "Create literature synopsis extracting key elements",
            "Identify commonalities and literature gaps",
            "Draft 2-3 potential research questions",
            "Practice 3-sentence elevator pitch for project"
        ]
    },
    'research_question': {
        'name': 'Research Question Development',
        'description': 'Problem formulation and question refinement',
        'icon': '❓',
        'default_duration_weeks': 2,
        'task_types': ['analysis', 'writing', 'consultation'],
        'task_templates': [
            "Finalize specific research question with adviser feedback",
            "Clarify if question is empirical, theoretical, or both",
            "Identify key concepts and variables",
            "Determine sociological significance of question",
            "Draft one-paragraph research gap statement",
            "Refine research question based on literature gaps",
            "Develop theoretical framework outline",
            "Create research question justification document",
            "Meet with advisor to validate research direction",
            "Prepare research question presentation for peers"
        ]
    },
    'methods_planning': {
        'name': 'Methods Planning',
        'description': 'Research design and methodology development',
        'icon': '🔬',
        'default_duration_weeks': 3,
        'task_types': ['design', 'planning', 'validation'],
        'task_templates': [
            "Choose primary research method",
            "Identify validated instruments from literature",
            "Collect examples of similar studies and methods",
            "Draft Methods section outline (sampling, procedure, instruments)",
            "Review methodological blueprints",
            "Draft survey, interview guide, or observation plan",
            "Design backwards from hypothetical results",
            "Calculate sample size and feasibility constraints",
            "Create data collection strategy",
            "Meet with adviser for methods input",
            "Pilot instruments with 3-5 participants",
            "Refine based on clarity and usefulness",
            "Finalize sampling criteria and recruitment methods",
            "Create project timeline for data collection",
            "Document methodology decisions and rationale"
        ]
    },
    'irb_proposal': {
        'name': 'IRB Proposal',
        'description': 'Ethics review and compliance documentation',
        'icon': '📋',
        'default_duration_weeks': 2,
        'task_types': ['documentation', 'compliance', 'submission'],
        'task_templates': [
            "Complete CITI training or ethics certification",
            "Draft informed consent forms",
            "Prepare risk assessment documentation",
            "Compile IRB application materials",
            "Submit IRB application and respond to feedback",
            "Begin preparing IRB materials",
            "Draft consent forms and recruitment scripts",
            "Prepare and compile all IRB documents",
            "Get adviser feedback on IRB documents",
            "Submit IRB application",
            "Revise IRB materials based on feedback",
            "Finalize all compliance documentation"
        ]
    }
}

class PhaseManager:
    """Manages phase lifecycle and validation for multi-phase projects"""
    
    @staticmethod
    def get_available_phases():
        """Get list of all available phase types"""
        return list(PHASE_TEMPLATES.keys())
    
    @staticmethod
    def get_phase_template(phase_type):
        """Get template configuration for a specific phase type"""
        return PHASE_TEMPLATES.get(phase_type)
    
    @staticmethod
    def create_phases_for_student(student_id, selected_phases, deadlines):
        """Create project phases for a student based on selections and deadlines"""
        phases_created = []
        
        # Validate deadlines first
        if not PhaseManager.validate_phase_deadlines(selected_phases, deadlines):
            raise ValueError("Phase deadlines are not in valid chronological order")
        
        # Create phases in order
        for order_index, phase_type in enumerate(selected_phases, 1):
            template = PhaseManager.get_phase_template(phase_type)
            if not template:
                raise ValueError(f"Unknown phase type: {phase_type}")
            
            phase = ProjectPhase(
                student_id=student_id,
                phase_type=phase_type,
                phase_name=template['name'],
                deadline=deadlines[phase_type],
                is_active=True,
                order_index=order_index,
                created_at=datetime.utcnow()
            )
            
            db.session.add(phase)
            phases_created.append(phase)
        
        db.session.commit()
        return phases_created
    
    @staticmethod
    def get_active_phases(student_id):
        """Get all active phases for a student, ordered by order_index"""
        return ProjectPhase.query.filter_by(
            student_id=student_id,
            is_active=True
        ).order_by(ProjectPhase.order_index).all()
    
    @staticmethod
    def validate_phase_deadlines(selected_phases, deadlines):
        """Validate that phase deadlines are in logical chronological order"""
        if not selected_phases or not deadlines:
            return False
        
        # Define the logical order of phases
        phase_order = ['literature_review', 'research_question', 'methods_planning', 'irb_proposal']
        
        # Filter to only selected phases in their logical order
        ordered_selected = [p for p in phase_order if p in selected_phases]
        
        # Check that deadlines are in chronological order
        previous_deadline = None
        for phase_type in ordered_selected:
            if phase_type not in deadlines:
                return False
            
            current_deadline = deadlines[phase_type]
            if previous_deadline and current_deadline <= previous_deadline:
                return False
            
            previous_deadline = current_deadline
        
        # Ensure all deadlines are in the future
        today = datetime.now().date()
        for deadline in deadlines.values():
            if deadline <= today:
                return False
        
        return True
    
    @staticmethod
    def migrate_legacy_student(student_id):
        """Migrate a legacy student to multi-phase system with Literature Review phase"""
        student = Student.query.get(student_id)
        if not student or student.is_multi_phase:
            return None
        
        if not student.onboarded or not student.lit_review_deadline:
            return None
        
        # Create Literature Review phase
        phase = ProjectPhase(
            student_id=student_id,
            phase_type=PhaseType.LITERATURE_REVIEW.value,
            phase_name="Literature Review",
            deadline=student.lit_review_deadline,
            is_active=True,
            order_index=1,
            created_at=datetime.utcnow()
        )
        
        db.session.add(phase)
        db.session.flush()  # Get the phase ID
        
        # Migrate existing ScheduleItem tasks to PhaseTask
        existing_tasks = ScheduleItem.query.filter_by(student_id=student_id).all()
        
        for task in existing_tasks:
            phase_task = PhaseTask(
                phase_id=phase.id,
                date=task.date,
                task_description=task.task_description,
                task_type='reading',  # Default to reading for literature review
                day_intensity=task.day_intensity,
                completed=task.completed,
                created_at=task.created_at
            )
            db.session.add(phase_task)
        
        # Mark student as migrated
        student.is_multi_phase = True
        db.session.commit()
        
        return phase
    
    @staticmethod
    def get_phase_progress(phase_id):
        """Calculate progress statistics for a phase"""
        phase = ProjectPhase.query.get(phase_id)
        if not phase:
            return None
        
        total_tasks = PhaseTask.query.filter_by(phase_id=phase_id).count()
        completed_tasks = PhaseTask.query.filter_by(phase_id=phase_id, completed=True).count()
        
        progress_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        return {
            'phase': phase,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'progress_percentage': round(progress_percentage, 1),
            'is_complete': progress_percentage == 100
        }

class PhaseTaskGenerator:
    """Generates phase-specific tasks and distributes them across work days"""
    
    @staticmethod
    def generate_tasks_for_phase(phase, work_preferences):
        """Generate tasks for a specific phase based on work preferences"""
        if not phase or not work_preferences:
            return []
        
        template = PhaseManager.get_phase_template(phase.phase_type)
        if not template:
            return []
        
        # Get task templates for this phase
        task_templates = template['task_templates']
        
        # Parse work preferences
        work_days = json.loads(work_preferences) if isinstance(work_preferences, str) else work_preferences
        
        # Generate tasks distributed across available work days
        tasks = PhaseTaskGenerator.distribute_tasks_by_intensity(
            task_templates, work_days, phase.deadline, phase.id
        )
        
        return tasks
    
    @staticmethod
    def get_task_template(phase_type):
        """Get task templates for a specific phase type"""
        template = PhaseManager.get_phase_template(phase_type)
        return template['task_templates'] if template else []
    
    @staticmethod
    def distribute_tasks_by_intensity(task_templates, work_days, deadline, phase_id):
        """Distribute tasks evenly across work days with intelligent load balancing"""
        if not task_templates or not work_days:
            return []
        
        # Get all available work days between now and deadline
        available_days = PhaseTaskGenerator._get_available_work_days(work_days, deadline)
        
        if not available_days:
            return []
        
        total_tasks = len(task_templates)
        total_days = len(available_days)
        
        # Calculate task distribution
        task_distribution = PhaseTaskGenerator._calculate_task_distribution(
            total_tasks, available_days
        )
        
        # Create tasks based on the distribution
        tasks = []
        task_index = 0
        
        for day_info in task_distribution:
            tasks_for_day = day_info['task_count']
            
            for _ in range(tasks_for_day):
                if task_index < total_tasks:
                    task = PhaseTask(
                        phase_id=phase_id,
                        date=day_info['date'],
                        task_description=task_templates[task_index],
                        task_type=PhaseTaskGenerator._determine_task_type(task_templates[task_index]),
                        day_intensity=day_info['intensity'],
                        priority=PhaseTaskGenerator._determine_task_priority(task_templates[task_index], task_index, len(task_templates)),
                        completed=False,
                        created_at=datetime.utcnow()
                    )
                    tasks.append(task)
                    task_index += 1
        
        return tasks
    
    @staticmethod
    def _get_available_work_days(work_days, deadline):
        """Get all available work days between now and deadline"""
        available_days = []
        current_date = datetime.now().date()
        end_date = deadline
        
        while current_date <= end_date:
            day_name = current_date.strftime('%A').lower()
            day_intensity = work_days.get(day_name, 'none')
            
            if day_intensity != 'none':
                available_days.append({
                    'date': current_date,
                    'intensity': day_intensity,
                    'day_name': day_name
                })
            
            current_date += timedelta(days=1)
        
        return available_days
    
    @staticmethod
    def _calculate_task_distribution(total_tasks, available_days):
        """Calculate intelligent task distribution across available days"""
        if not available_days or total_tasks == 0:
            return []
        
        total_days = len(available_days)
        
        # Separate light and heavy days
        light_days = [day for day in available_days if day['intensity'] == 'light']
        heavy_days = [day for day in available_days if day['intensity'] == 'heavy']
        
        # Calculate base distribution (evenly spread)
        base_tasks_per_day = total_tasks // total_days
        extra_tasks = total_tasks % total_days
        
        # Create distribution plan
        distribution = []
        
        # If we have more tasks than days, we need to distribute intelligently
        if total_tasks > total_days:
            # Calculate capacity ratios (heavy days can handle more)
            light_capacity_weight = 1.0
            heavy_capacity_weight = 2.0
            
            # Calculate total capacity weights
            total_capacity = (len(light_days) * light_capacity_weight + 
                            len(heavy_days) * heavy_capacity_weight)
            
            # Distribute tasks proportionally
            for day in available_days:
                if day['intensity'] == 'light':
                    # Light days get proportionally fewer tasks
                    task_count = max(1, int((total_tasks * light_capacity_weight) / total_capacity))
                else:  # heavy day
                    # Heavy days get proportionally more tasks
                    task_count = max(1, int((total_tasks * heavy_capacity_weight) / total_capacity))
                
                distribution.append({
                    'date': day['date'],
                    'intensity': day['intensity'],
                    'task_count': task_count
                })
            
            # Adjust for any rounding differences
            assigned_tasks = sum(d['task_count'] for d in distribution)
            remaining_tasks = total_tasks - assigned_tasks
            
            # Distribute remaining tasks, preferring heavy days
            day_index = 0
            while remaining_tasks > 0:
                # Prefer heavy days for extra tasks
                if distribution[day_index]['intensity'] == 'heavy' or len(heavy_days) == 0:
                    distribution[day_index]['task_count'] += 1
                    remaining_tasks -= 1
                day_index = (day_index + 1) % len(distribution)
        
        else:
            # We have fewer or equal tasks than days - distribute evenly
            for i, day in enumerate(available_days):
                task_count = base_tasks_per_day
                # Distribute extra tasks to the first few days
                if i < extra_tasks:
                    task_count += 1
                
                distribution.append({
                    'date': day['date'],
                    'intensity': day['intensity'],
                    'task_count': task_count
                })
        
        # Remove days with 0 tasks and sort by date
        distribution = [d for d in distribution if d['task_count'] > 0]
        distribution.sort(key=lambda x: x['date'])
        
        return distribution
    
    @staticmethod
    def _determine_task_type(task_description):
        """Determine task type based on task description keywords"""
        task_lower = task_description.lower()
        
        # Documentation/compliance tasks (check first for specificity)
        if any(keyword in task_lower for keyword in ['irb', 'consent', 'compliance', 'ethics', 'submit']):
            return 'documentation'
        
        # Meeting/consultation tasks (check before writing to avoid conflicts)
        elif any(keyword in task_lower for keyword in ['meet', 'discuss', 'adviser', 'advisor', 'feedback']):
            return 'consultation'
        
        # Writing-related tasks (more specific keywords first)
        elif any(keyword in task_lower for keyword in ['draft', 'write', 'document methodology', 'outline']):
            return 'writing'
        
        # Reading-related tasks
        elif any(keyword in task_lower for keyword in ['read', 'skim', 'article', 'source', 'literature']):
            return 'reading'
        
        # Research-related tasks
        elif any(keyword in task_lower for keyword in ['research', 'identify', 'collect', 'find', 'search']):
            return 'research'
        
        # Analysis-related tasks
        elif any(keyword in task_lower for keyword in ['analyze', 'synthesis', 'organize', 'compare', 'evaluate']):
            return 'analysis'
        
        # Design/planning tasks
        elif any(keyword in task_lower for keyword in ['design', 'plan', 'create', 'develop', 'method']):
            return 'design'
        
        # Default to general
        else:
            return 'general'
    
    @staticmethod
    def _determine_task_priority(task_description, task_index, total_tasks):
        """Determine task priority based on description and position in timeline"""
        task_lower = task_description.lower()
        
        # High priority keywords
        high_priority_keywords = [
            'deadline', 'urgent', 'critical', 'important', 'due', 'submit', 
            'approval', 'irb', 'ethics', 'committee', 'proposal', 'defense'
        ]
        
        # Low priority keywords  
        low_priority_keywords = [
            'optional', 'extra', 'additional', 'supplementary', 'bonus',
            'explore', 'consider', 'maybe', 'if time'
        ]
        
        # Check for explicit priority keywords
        if any(word in task_lower for word in high_priority_keywords):
            return 'high'
        
        if any(word in task_lower for word in low_priority_keywords):
            return 'low'
        
        # Priority based on position in timeline
        # First 20% of tasks are high priority (foundational work)
        # Last 20% of tasks are high priority (final deliverables)
        # Middle 60% are medium priority
        position_ratio = task_index / max(1, total_tasks - 1)
        
        if position_ratio <= 0.2 or position_ratio >= 0.8:
            return 'high'
        
        return 'medium'
    
    @staticmethod
    def adjust_tasks_for_dependencies(phase_tasks):
        """Adjust task scheduling based on phase dependencies (future enhancement)"""
        # This method can be enhanced later to handle inter-phase dependencies
        # For now, it returns tasks as-is
        return phase_tasks
    
    @staticmethod
    def create_and_save_tasks_for_phase(phase, work_preferences):
        """Generate and save tasks for a phase to the database"""
        tasks = PhaseTaskGenerator.generate_tasks_for_phase(phase, work_preferences)
        
        # Save tasks to database
        for task in tasks:
            db.session.add(task)
        
        try:
            db.session.commit()
            return tasks
        except Exception as e:
            db.session.rollback()
            raise e

class LegacyScheduleAdapter:
    """Adapter to maintain compatibility with existing ScheduleItem queries"""
    
    @staticmethod
    def get_student_tasks(student_id, date=None, completed=None):
        """Returns tasks from both old ScheduleItem and new PhaseTask models"""
        student = Student.query.get(student_id)
        if not student:
            return []
        
        if student.is_multi_phase:
            # Use new PhaseTask model
            query = db.session.query(PhaseTask).join(ProjectPhase).filter(
                ProjectPhase.student_id == student_id
            )
            
            if date:
                query = query.filter(PhaseTask.date == date)
            
            if completed is not None:
                query = query.filter(PhaseTask.completed == completed)
            
            return query.all()
        else:
            # Use legacy ScheduleItem model
            query = ScheduleItem.query.filter_by(student_id=student_id)
            
            if date:
                query = query.filter_by(date=date)
            
            if completed is not None:
                query = query.filter_by(completed=completed)
            
            return query.all()
    
    @staticmethod
    def get_upcoming_tasks(student_id, limit=7):
        """Get upcoming incomplete tasks for a student"""
        today = datetime.now().date()
        student = Student.query.get(student_id)
        
        if not student:
            return []
        
        if student.is_multi_phase:
            # Use new PhaseTask model
            return db.session.query(PhaseTask).join(ProjectPhase).filter(
                ProjectPhase.student_id == student_id,
                PhaseTask.completed == False,
                PhaseTask.date >= today
            ).order_by(PhaseTask.date).limit(limit).all()
        else:
            # Use legacy ScheduleItem model
            return ScheduleItem.query.filter(
                ScheduleItem.student_id == student_id,
                ScheduleItem.completed == False,
                ScheduleItem.date >= today
            ).order_by(ScheduleItem.date).limit(limit).all()
    
    @staticmethod
    def get_tasks_by_date_range(student_id, start_date, end_date):
        """Get tasks within a date range"""
        student = Student.query.get(student_id)
        
        if not student:
            return []
        
        if student.is_multi_phase:
            # Use new PhaseTask model
            return db.session.query(PhaseTask).join(ProjectPhase).filter(
                ProjectPhase.student_id == student_id,
                PhaseTask.date >= start_date,
                PhaseTask.date <= end_date
            ).order_by(PhaseTask.date).all()
        else:
            # Use legacy ScheduleItem model
            return ScheduleItem.query.filter(
                ScheduleItem.student_id == student_id,
                ScheduleItem.date >= start_date,
                ScheduleItem.date <= end_date
            ).order_by(ScheduleItem.date).all()
    
    @staticmethod
    def mark_task_completed(task_id, is_multi_phase=None):
        """Mark a task as completed, handling both old and new models"""
        if is_multi_phase is None:
            # Try to determine from task type
            phase_task = PhaseTask.query.get(task_id)
            if phase_task:
                phase_task.completed = True
                db.session.commit()
                return True
            
            schedule_item = ScheduleItem.query.get(task_id)
            if schedule_item:
                schedule_item.completed = True
                db.session.commit()
                return True
            
            return False
        elif is_multi_phase:
            # Use PhaseTask model
            task = PhaseTask.query.get(task_id)
            if task:
                task.completed = True
                db.session.commit()
                return True
        else:
            # Use ScheduleItem model
            task = ScheduleItem.query.get(task_id)
            if task:
                task.completed = True
                db.session.commit()
                return True
        
        return False
    
    @staticmethod
    def get_task_counts(student_id):
        """Get task completion statistics"""
        student = Student.query.get(student_id)
        
        if not student:
            return {'total': 0, 'completed': 0, 'remaining': 0}
        
        if student.is_multi_phase:
            # Use new PhaseTask model
            total = db.session.query(PhaseTask).join(ProjectPhase).filter(
                ProjectPhase.student_id == student_id
            ).count()
            
            completed = db.session.query(PhaseTask).join(ProjectPhase).filter(
                ProjectPhase.student_id == student_id,
                PhaseTask.completed == True
            ).count()
        else:
            # Use legacy ScheduleItem model
            total = ScheduleItem.query.filter_by(student_id=student_id).count()
            completed = ScheduleItem.query.filter_by(student_id=student_id, completed=True).count()
        
        return {
            'total': total,
            'completed': completed,
            'remaining': total - completed
        }

class MigrationService:
    """Service for migrating legacy students to multi-phase system"""
    
    @staticmethod
    def migrate_student_to_multiphase(student_id):
        """Migrate a legacy student to multi-phase system"""
        student = Student.query.get(student_id)
        if not student or student.is_multi_phase:
            return None
        
        if not student.onboarded or not student.lit_review_deadline:
            return None
        
        try:
            # Create Literature Review phase using PhaseManager
            phase = ProjectPhase(
                student_id=student_id,
                phase_type=PhaseType.LITERATURE_REVIEW.value,
                phase_name="Literature Review",
                deadline=student.lit_review_deadline,
                is_active=True,
                order_index=1,
                created_at=datetime.utcnow()
            )
            
            db.session.add(phase)
            db.session.flush()  # Get the phase ID
            
            # Migrate existing ScheduleItem tasks to PhaseTask
            existing_tasks = ScheduleItem.query.filter_by(student_id=student_id).all()
            
            for task in existing_tasks:
                phase_task = PhaseTask(
                    phase_id=phase.id,
                    date=task.date,
                    task_description=task.task_description,
                    task_type=PhaseTaskGenerator._determine_task_type(task.task_description),
                    day_intensity=task.day_intensity,
                    completed=task.completed,
                    created_at=task.created_at
                )
                db.session.add(phase_task)
            
            # Mark student as migrated
            student.is_multi_phase = True
            db.session.commit()
            
            return {
                'phase': phase,
                'migrated_tasks': len(existing_tasks),
                'success': True
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'error': str(e),
                'success': False
            }
    
    @staticmethod
    def can_migrate_student(student_id):
        """Check if a student can be migrated to multi-phase system"""
        student = Student.query.get(student_id)
        
        if not student:
            return False, "Student not found"
        
        if student.is_multi_phase:
            return False, "Student already using multi-phase system"
        
        if not student.onboarded:
            return False, "Student not onboarded"
        
        if not student.lit_review_deadline:
            return False, "No literature review deadline set"
        
        return True, "Student can be migrated"
    
    @staticmethod
    def get_migration_preview(student_id):
        """Preview what would happen during migration"""
        student = Student.query.get(student_id)
        
        if not student:
            return None
        
        existing_tasks = ScheduleItem.query.filter_by(student_id=student_id).all()
        
        # Analyze existing tasks
        task_analysis = {
            'total_tasks': len(existing_tasks),
            'completed_tasks': len([t for t in existing_tasks if t.completed]),
            'pending_tasks': len([t for t in existing_tasks if not t.completed]),
            'date_range': {
                'earliest': min([t.date for t in existing_tasks]) if existing_tasks else None,
                'latest': max([t.date for t in existing_tasks]) if existing_tasks else None
            },
            'task_types': {}
        }
        
        # Analyze task types that would be assigned
        for task in existing_tasks:
            task_type = PhaseTaskGenerator._determine_task_type(task.task_description)
            task_analysis['task_types'][task_type] = task_analysis['task_types'].get(task_type, 0) + 1
        
        return {
            'student': {
                'name': student.name,
                'email': student.email,
                'lit_review_deadline': student.lit_review_deadline,
                'thesis_deadline': student.thesis_deadline
            },
            'migration_plan': {
                'will_create_phase': 'Literature Review',
                'phase_deadline': student.lit_review_deadline,
                'tasks_to_migrate': task_analysis
            }
        }
    
    @staticmethod
    def rollback_migration(student_id):
        """Rollback a student migration (for testing/emergency use)"""
        student = Student.query.get(student_id)
        
        if not student or not student.is_multi_phase:
            return False, "Student not in multi-phase system"
        
        try:
            # Get all phases for this student
            phases = ProjectPhase.query.filter_by(student_id=student_id).all()
            
            # Delete all phase tasks and phases
            for phase in phases:
                PhaseTask.query.filter_by(phase_id=phase.id).delete()
                db.session.delete(phase)
            
            # Mark student as legacy
            student.is_multi_phase = False
            db.session.commit()
            
            return True, f"Rolled back migration for {student.name}"
            
        except Exception as e:
            db.session.rollback()
            return False, f"Rollback failed: {str(e)}"

@login_manager.user_loader
def load_user(user_id):
    return Student.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.onboarded:
            return redirect(url_for('dashboard'))
        else:
            return redirect(url_for('onboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        
        # Check if user already exists
        if Student.query.filter_by(email=email).first():
            flash('Email address already exists')
            return render_template('register.html')
        
        # Create new user
        student = Student(name=name, email=email)
        student.set_password(password)
        db.session.add(student)
        db.session.commit()
        
        login_user(student)
        return redirect(url_for('onboard'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        student = Student.query.filter_by(email=email).first()
        
        if student and student.check_password(password):
            login_user(student)
            if student.onboarded:
                return redirect(url_for('dashboard'))
            else:
                return redirect(url_for('onboard'))
        else:
            flash('Invalid email or password')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        student = Student.query.filter_by(email=email).first()
        
        if student:
            # Generate reset token
            token = student.generate_reset_token()
            db.session.commit()
            
            # Create reset URL
            reset_url = url_for('reset_password', token=token, _external=True)
            
            # Email content
            subject = "PaperPacer - Password Reset Request"
            
            body_text = f"""
Hello {student.name},

You requested a password reset for your PaperPacer account.

Click the following link to reset your password:
{reset_url}

This link will expire in 1 hour for security reasons.

If you didn't request this reset, please ignore this email.

Best regards,
The PaperPacer Team
            """.strip()
            
            body_html = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #6366f1;">PaperPacer - Password Reset</h2>
                    
                    <p>Hello <strong>{student.name}</strong>,</p>
                    
                    <p>You requested a password reset for your PaperPacer account.</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{reset_url}" 
                           style="background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%); 
                                  color: white; 
                                  padding: 12px 30px; 
                                  text-decoration: none; 
                                  border-radius: 8px; 
                                  display: inline-block;
                                  font-weight: 500;">
                            🔑 Reset Your Password
                        </a>
                    </div>
                    
                    <p><small>This link will expire in <strong>1 hour</strong> for security reasons.</small></p>
                    
                    <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                    
                    <p><small>If you didn't request this reset, please ignore this email.</small></p>
                    
                    <p><small>Best regards,<br>The PaperPacer Team</small></p>
                </div>
            </body>
            </html>
            """.strip()
            
            # Send email
            email_sent = send_email(student.email, subject, body_text, body_html)
            
            if not email_sent and app.config.get('MAIL_ENABLED', False):
                flash('There was an error sending the reset email. Please try again later.', 'error')
                return render_template('forgot_password.html')
            
            # For development/testing - also show the link in flash message
            if not app.config.get('MAIL_ENABLED', False):
                flash(f'Email sending disabled. Reset link: {reset_url}', 'info')
        
        # Always show the same message for security (don't reveal if email exists)
        flash('If an account with this email exists, we\'ve sent a password reset link.', 'success')
        return redirect(url_for('login'))
    
    return render_template('forgot_password.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    student = Student.query.filter_by(reset_token=token).first()
    
    if not student or not student.verify_reset_token(token):
        flash('Invalid or expired reset token.', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('reset_password.html', token=token)
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return render_template('reset_password.html', token=token)
        
        # Update password and clear reset token
        student.set_password(password)
        student.clear_reset_token()
        db.session.commit()
        
        flash('Your password has been reset successfully. You can now log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('reset_password.html', token=token)

@app.route('/onboard')
@login_required
def onboard():
    if current_user.onboarded:
        return redirect(url_for('dashboard'))
    return render_template('onboard.html')

@app.route('/submit_onboarding', methods=['POST'])
@login_required
def submit_onboarding():
    try:
        # Update current user with basic project data
        current_user.project_title = request.form['project_title']
        thesis_deadline = datetime.strptime(request.form['thesis_deadline'], '%Y-%m-%d').date()
        
        # Process work days with intensity levels
        work_day_preferences = {}
        for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']:
            intensity = request.form.get(f'{day}_intensity', 'none')
            if intensity != 'none':
                work_day_preferences[day] = intensity
        current_user.work_days = json.dumps(work_day_preferences)
        
        # Get selected phases and their deadlines
        selected_phases = request.form.getlist('selected_phases')
        if not selected_phases:
            flash('Please select at least one research phase')
            return render_template('onboard.html')
        
        # Collect phase deadlines
        phase_deadlines = {}
        for phase_type in selected_phases:
            deadline_str = request.form.get(f'{phase_type}_deadline')
            if not deadline_str:
                flash(f'Please set a deadline for {PhaseManager.get_phase_template(phase_type)["name"]}')
                return render_template('onboard.html')
            
            phase_deadlines[phase_type] = datetime.strptime(deadline_str, '%Y-%m-%d').date()
        
        # Validate thesis deadline is in the future
        today = datetime.now().date()
        if thesis_deadline <= today:
            flash('Thesis deadline must be in the future')
            return render_template('onboard.html')
        
        # Validate phase deadlines using PhaseManager
        if not PhaseManager.validate_phase_deadlines(selected_phases, phase_deadlines):
            flash('Phase deadlines must be in chronological order and in the future')
            return render_template('onboard.html')
        
        # Validate all phase deadlines are before thesis deadline
        for phase_type, deadline in phase_deadlines.items():
            if deadline >= thesis_deadline:
                template = PhaseManager.get_phase_template(phase_type)
                phase_name = template['name'] if template else phase_type
                flash(f'{phase_name} deadline must be before thesis deadline')
                return render_template('onboard.html')
        
        # Save basic student data
        current_user.thesis_deadline = thesis_deadline
        # Keep lit_review_deadline for backward compatibility
        if 'literature_review' in phase_deadlines:
            current_user.lit_review_deadline = phase_deadlines['literature_review']
        current_user.onboarded = True
        current_user.is_multi_phase = True  # Mark as multi-phase user
        
        db.session.commit()
        
        # Create phases using PhaseManager
        phases = PhaseManager.create_phases_for_student(
            current_user.id, selected_phases, phase_deadlines
        )
        
        # Generate tasks for each phase
        for phase in phases:
            PhaseTaskGenerator.create_and_save_tasks_for_phase(phase, work_day_preferences)
        
        flash(f'Successfully created your project with {len(phases)} research phases!')
        return redirect(url_for('dashboard'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred during setup: {str(e)}')
        return render_template('onboard.html')

@app.route('/dashboard')
@login_required
def dashboard():
    if not current_user.onboarded:
        return redirect(url_for('onboard'))
    
    # Get upcoming tasks using LegacyScheduleAdapter for compatibility
    upcoming_tasks = LegacyScheduleAdapter.get_upcoming_tasks(current_user.id, limit=7)
    
    today = datetime.now().date()
    
    return render_template('dashboard.html',
                         student=current_user,
                         upcoming_tasks=upcoming_tasks,
                         today=today,
                         get_phase_progress=get_phase_progress,
                         get_total_task_count=get_total_task_count,
                         get_completed_task_count=get_completed_task_count,
                         get_next_deadline=get_next_deadline)

# Helper functions for template
def get_phase_progress(phase_id):
    return PhaseManager.get_phase_progress(phase_id)

def get_phase_icon(phase_type):
    template = PhaseManager.get_phase_template(phase_type)
    return template['icon'] if template else '📋'

def get_next_deadline(phases):
    if not phases:
        return None
    
    today = datetime.now().date()
    upcoming_phases = [p for p in phases if p.deadline >= today and p.is_active]
    
    if upcoming_phases:
        return min(upcoming_phases, key=lambda p: p.deadline)
    return None

def get_total_task_count(student_id):
    if current_user.is_multi_phase:
        return db.session.query(PhaseTask).join(ProjectPhase).filter(
            ProjectPhase.student_id == student_id
        ).count()
    else:
        return ScheduleItem.query.filter_by(student_id=student_id).count()

def get_completed_task_count(student_id):
    if current_user.is_multi_phase:
        return db.session.query(PhaseTask).join(ProjectPhase).filter(
            ProjectPhase.student_id == student_id,
            PhaseTask.completed == True
        ).count()
    else:
        return ScheduleItem.query.filter_by(student_id=student_id, completed=True).count()

@app.context_processor
def inject_template_functions():
    """Inject utility functions into template context"""
    return {
        'get_phase_icon': get_phase_icon,
        'get_phase_progress': get_phase_progress,
        'get_total_task_count': get_total_task_count,
        'get_completed_task_count': get_completed_task_count,
        'get_next_deadline': get_next_deadline
    }

@app.route('/phase/<int:phase_id>')
@login_required
def phase_detail(phase_id):
    """View details for a specific phase"""
    if not current_user.onboarded:
        return redirect(url_for('onboard'))
    
    # Get the phase and verify it belongs to current user
    phase = ProjectPhase.query.filter_by(id=phase_id, student_id=current_user.id).first()
    if not phase:
        flash('Phase not found')
        return redirect(url_for('dashboard'))
    
    # Get tasks for this phase
    phase_tasks = PhaseTask.query.filter_by(phase_id=phase_id).order_by(PhaseTask.date).all()
    
    # Get phase progress
    progress = PhaseManager.get_phase_progress(phase_id)
    
    # Get phase template for additional info
    template = PhaseManager.get_phase_template(phase.phase_type)
    
    today = datetime.now().date()
    
    return render_template('phase_detail.html',
                         phase=phase,
                         phase_tasks=phase_tasks,
                         progress=progress,
                         template=template,
                         today=today)

@app.route('/timeline')
@login_required
def integrated_timeline():
    """View integrated timeline across all phases"""
    if not current_user.onboarded:
        return redirect(url_for('onboard'))
    
    if not current_user.is_multi_phase:
        flash('Timeline view is only available for multi-phase projects')
        return redirect(url_for('dashboard'))
    
    try:
        timeline_data = create_timeline_visualization_data(current_user.id)
        return render_template('timeline.html', 
                             timeline_data=timeline_data,
                             student=current_user)
    except Exception as e:
        flash(f'Error loading timeline: {str(e)}')
        return redirect(url_for('dashboard'))

@app.route('/api/timeline/<int:student_id>')
@login_required
def api_timeline_data(student_id):
    """API endpoint for timeline data (for AJAX updates)"""
    if student_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    if not current_user.is_multi_phase:
        return jsonify({'error': 'Multi-phase project required'}), 400
    
    try:
        timeline_data = create_timeline_visualization_data(student_id)
        return jsonify(timeline_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/redistribute_tasks', methods=['POST'])
@login_required
def api_redistribute_tasks():
    """API endpoint for automatic task redistribution"""
    data = request.get_json()
    
    if not data or 'phase_id' not in data or 'new_deadline' not in data:
        return jsonify({'error': 'Missing required parameters'}), 400
    
    try:
        phase_id = int(data['phase_id'])
        new_deadline = datetime.strptime(data['new_deadline'], '%Y-%m-%d').date()
        
        # Verify phase belongs to current user
        phase = ProjectPhase.query.get(phase_id)
        if not phase or phase.student_id != current_user.id:
            return jsonify({'error': 'Phase not found or access denied'}), 403
        
        coordinator = ScheduleCoordinator(current_user.id)
        result = coordinator.redistribute_tasks_after_deadline_change(phase_id, new_deadline)
        
        return jsonify(result)
        
    except ValueError as e:
        return jsonify({'error': f'Invalid data: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Redistribution failed: {str(e)}'}), 500

@app.route('/daily_checkin')
@login_required
def daily_checkin():
    if not current_user.onboarded:
        return redirect(url_for('onboard'))
    
    today = datetime.now().date()
    
    if current_user.is_multi_phase:
        # Use new PhaseTask model
        today_tasks = db.session.query(PhaseTask).join(ProjectPhase).filter(
            ProjectPhase.student_id == current_user.id,
            PhaseTask.date == today
        ).all()
    else:
        # Legacy single-phase support
        today_tasks = ScheduleItem.query.filter_by(
            student_id=current_user.id,
            date=today
        ).all()
    
    return render_template('daily_checkin.html', student=current_user, today_tasks=today_tasks, today=today)

@app.route('/day/<date_str>')
@login_required
def day_detail(date_str):
    if not current_user.onboarded:
        return redirect(url_for('onboard'))
    
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        flash('Invalid date format')
        return redirect(url_for('dashboard'))
    
    # Get tasks for this date
    if current_user.is_multi_phase:
        # Use new PhaseTask model
        day_tasks = db.session.query(PhaseTask).join(ProjectPhase).filter(
            ProjectPhase.student_id == current_user.id,
            PhaseTask.date == selected_date
        ).all()
    else:
        # Legacy single-phase support
        day_tasks = ScheduleItem.query.filter_by(
            student_id=current_user.id,
            date=selected_date
        ).all()
    
    # Check if this is today for special handling
    today = datetime.now().date()
    is_today = selected_date == today
    
    return render_template('day_detail.html', 
                         student=current_user, 
                         selected_date=selected_date,
                         day_tasks=day_tasks,
                         is_today=is_today,
                         today=today)

@app.route('/remaining_tasks')
@login_required
def remaining_tasks():
    if not current_user.onboarded:
        return redirect(url_for('onboard'))
    
    # Get phase filter parameter
    phase_filter = request.args.get('phase', type=int)
    
    # Get all incomplete tasks, organized by date
    if current_user.is_multi_phase:
        # Use new PhaseTask model with optional phase filtering
        query = db.session.query(PhaseTask).join(ProjectPhase).filter(
            ProjectPhase.student_id == current_user.id,
            PhaseTask.completed == False
        )
        
        if phase_filter:
            query = query.filter(PhaseTask.phase_id == phase_filter)
            
        incomplete_tasks = query.order_by(PhaseTask.date).all()
        
        # Get total tasks for completion rate calculation
        total_query = db.session.query(PhaseTask).join(ProjectPhase).filter(
            ProjectPhase.student_id == current_user.id
        )
        if phase_filter:
            total_query = total_query.filter(PhaseTask.phase_id == phase_filter)
        total_tasks = total_query.count()
        
        # Get user's phases for filtering dropdown
        user_phases = ProjectPhase.query.filter_by(
            student_id=current_user.id,
            is_active=True
        ).order_by(ProjectPhase.order_index).all()
        
    else:
        # Legacy single-phase support
        incomplete_tasks = ScheduleItem.query.filter_by(
            student_id=current_user.id,
            completed=False
        ).order_by(ScheduleItem.date).all()
        
        total_tasks = ScheduleItem.query.filter_by(student_id=current_user.id).count()
        user_phases = []
    
    # Group tasks by different categories for better organization
    today = datetime.now().date()
    
    overdue_tasks = [task for task in incomplete_tasks if task.date < today]
    today_tasks = [task for task in incomplete_tasks if task.date == today]
    upcoming_tasks = [task for task in incomplete_tasks if task.date > today]
    
    # Group upcoming tasks by week for better display
    upcoming_by_week = {}
    for task in upcoming_tasks:
        # Calculate the Monday of the week this task falls in
        week_start = task.date - timedelta(days=task.date.weekday())
        week_key = week_start.strftime('%Y-%m-%d')
        if week_key not in upcoming_by_week:
            upcoming_by_week[week_key] = {
                'week_start': week_start,
                'tasks': []
            }
        upcoming_by_week[week_key]['tasks'].append(task)
    
    # Sort weeks by date
    upcoming_weeks = sorted(upcoming_by_week.items(), key=lambda x: x[1]['week_start'])
    
    # Calculate some stats
    total_incomplete = len(incomplete_tasks)
    completion_rate = ((total_tasks - total_incomplete) / total_tasks * 100) if total_tasks > 0 else 0
    
    # Get selected phase info for display
    selected_phase = None
    if phase_filter and current_user.is_multi_phase:
        selected_phase = ProjectPhase.query.get(phase_filter)
    
    return render_template('remaining_tasks.html', 
                         student=current_user,
                         overdue_tasks=overdue_tasks,
                         today_tasks=today_tasks,
                         upcoming_tasks=upcoming_tasks,
                         upcoming_weeks=upcoming_weeks,
                         total_incomplete=total_incomplete,
                         completion_rate=completion_rate,
                         today=today,
                         user_phases=user_phases,
                         selected_phase=selected_phase,
                         phase_filter=phase_filter)

@app.route('/settings')
@login_required
def settings():
    if not current_user.onboarded:
        return redirect(url_for('onboard'))
    return render_template('settings.html', student=current_user)

@app.route('/update_settings', methods=['POST'])
@login_required
def update_settings():
    # Update user settings
    current_user.project_title = request.form['project_title']
    current_user.thesis_deadline = datetime.strptime(request.form['thesis_deadline'], '%Y-%m-%d').date()
    
    # Handle multi-phase vs legacy settings
    if current_user.is_multi_phase:
        # Handle phase management
        try:
            # Process phase deletions
            delete_phase_ids = request.form.getlist('delete_phase_ids')
            for phase_id in delete_phase_ids:
                phase = ProjectPhase.query.get(int(phase_id))
                if phase and phase.student_id == current_user.id:
                    # Delete associated tasks
                    PhaseTask.query.filter_by(phase_id=phase.id).delete()
                    db.session.delete(phase)
            
            # Process existing phase updates
            existing_phase_ids = request.form.getlist('existing_phase_ids')
            for phase_id in existing_phase_ids:
                if phase_id not in delete_phase_ids:  # Skip deleted phases
                    phase = ProjectPhase.query.get(int(phase_id))
                    if phase and phase.student_id == current_user.id:
                        phase.phase_name = request.form.get(f'phase_name_{phase_id}', phase.phase_name)
                        new_deadline = request.form.get(f'phase_deadline_{phase_id}')
                        if new_deadline:
                            phase.deadline = datetime.strptime(new_deadline, '%Y-%m-%d').date()
            
            # Process new phases
            new_phase_counters = request.form.getlist('new_phase_counter')
            for counter in new_phase_counters:
                phase_name = request.form.get(f'new_phase_name_{counter}')
                phase_type = request.form.get(f'new_phase_type_{counter}')
                phase_deadline = request.form.get(f'new_phase_deadline_{counter}')
                
                if phase_name and phase_type and phase_deadline:
                    # Get next order index
                    max_order = db.session.query(db.func.max(ProjectPhase.order_index)).filter_by(
                        student_id=current_user.id
                    ).scalar() or 0
                    
                    new_phase = ProjectPhase(
                        student_id=current_user.id,
                        phase_type=phase_type,
                        phase_name=phase_name,
                        deadline=datetime.strptime(phase_deadline, '%Y-%m-%d').date(),
                        order_index=max_order + 1,
                        is_active=True
                    )
                    db.session.add(new_phase)
            
        except Exception as e:
            flash(f'Error updating phases: {str(e)}')
            return redirect(url_for('settings'))
    else:
        # Legacy single-phase settings
        current_user.lit_review_deadline = datetime.strptime(request.form['lit_review_deadline'], '%Y-%m-%d').date()
        
        # Validate legacy dates
        today = datetime.now().date()
        if current_user.lit_review_deadline <= today:
            flash('Literature review deadline must be in the future')
            return redirect(url_for('settings'))
            
        if current_user.lit_review_deadline >= current_user.thesis_deadline:
            flash('Literature review deadline must be before thesis deadline')
            return redirect(url_for('settings'))
    
    # Process work days with intensity levels
    work_day_preferences = {}
    for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']:
        intensity = request.form.get(f'{day}_intensity', 'none')
        if intensity != 'none':
            work_day_preferences[day] = intensity
    current_user.work_days = json.dumps(work_day_preferences)
    
    # Validate thesis deadline
    today = datetime.now().date()
    if current_user.thesis_deadline <= today:
        flash('Thesis deadline must be in the future')
        return redirect(url_for('settings'))
    
    db.session.commit()
    
    # Regenerate schedule with new settings
    if current_user.is_multi_phase:
        # Delete existing incomplete phase tasks
        for phase in current_user.project_phases:
            PhaseTask.query.filter_by(phase_id=phase.id, completed=False).delete()
        
        # Regenerate tasks for all phases
        for phase in current_user.project_phases:
            # Use existing task generation logic
            try:
                PhaseTaskGenerator.create_and_save_tasks_for_phase(phase, current_user.work_days)
            except Exception as e:
                # Fallback: create basic tasks if generator fails
                today = datetime.now().date()
                days_until_deadline = (phase.deadline - today).days
                if days_until_deadline > 0:
                    # Create a few basic tasks spread across the timeline
                    task_dates = [
                        today + timedelta(days=i * (days_until_deadline // 3))
                        for i in range(1, 4)
                        if today + timedelta(days=i * (days_until_deadline // 3)) <= phase.deadline
                    ]
                    
                    for i, task_date in enumerate(task_dates):
                        task = PhaseTask(
                            phase_id=phase.id,
                            date=task_date,
                            task_description=f"{phase.phase_name} Task {i+1}",
                            task_type="general",
                            day_intensity="light",
                            completed=False
                        )
                        db.session.add(task)
    else:
        # Legacy schedule regeneration
        ScheduleItem.query.filter_by(student_id=current_user.id, completed=False).delete()
        generate_schedule(current_user)
    
    db.session.commit()
    
    flash('Settings updated successfully! Your schedule has been regenerated.')
    return redirect(url_for('dashboard'))

@app.route('/submit_progress', methods=['POST'])
@login_required
def submit_progress():
    date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
    completed_tasks = request.form.getlist('completed_tasks')
    notes = request.form.get('notes', '')
    
    milestones_achieved = []
    phase_completions = []
    
    if current_user.is_multi_phase:
        # Basic multi-phase progress tracking
        progress_log = ProgressLog(
            student_id=current_user.id,
            date=date,
            tasks_completed=json.dumps(completed_tasks),
            notes=notes
        )
        db.session.add(progress_log)
        
        # Mark completed tasks
        for task_id in completed_tasks:
            task = PhaseTask.query.get(task_id)
            if task:
                phase = ProjectPhase.query.get(task.phase_id)
                if phase and phase.student_id == current_user.id:
                    task.completed = True
    else:
        # Legacy single-phase progress tracking
        progress_log = ProgressLog(
            student_id=current_user.id,
            date=date,
            tasks_completed=json.dumps(completed_tasks),
            notes=notes
        )
        db.session.add(progress_log)
        
        # Mark completed tasks
        for task_id in completed_tasks:
            task = ScheduleItem.query.get(task_id)
            if task and task.student_id == current_user.id:
                task.completed = True
    
    db.session.commit()
    
    # Check if schedule adjustment is needed
    adjust_schedule_if_needed(current_user.id, date, len(completed_tasks))
    
    # Create celebration messages for milestones and completions
    celebration_messages = []
    
    for milestone in milestones_achieved:
        celebration_messages.append(f"🎉 {milestone['celebration_message']}")
    
    for completion in phase_completions:
        celebration_messages.append(f"🏆 {completion['celebration_message']}")
    
    # Flash messages
    if celebration_messages:
        for message in celebration_messages:
            flash(message, 'success')
    else:
        flash('Progress submitted successfully!', 'success')
    
    # Redirect back to the day detail page if it's not today, otherwise go to dashboard
    if date == datetime.now().date():
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('day_detail', date_str=date.strftime('%Y-%m-%d')))

@app.route('/phase/<int:phase_id>/progress')
@login_required
def phase_progress_detail(phase_id):
    """View detailed progress for a specific phase"""
    if not current_user.onboarded or not current_user.is_multi_phase:
        return redirect(url_for('dashboard'))
    
    # Verify phase belongs to current user
    phase = ProjectPhase.query.filter_by(id=phase_id, student_id=current_user.id).first()
    if not phase:
        flash('Phase not found')
        return redirect(url_for('dashboard'))
    
    try:
        # Get basic progress information
        progress_summary = PhaseManager.get_phase_progress(phase_id)
        
        return render_template('phase_progress.html',
                             phase=phase,
                             progress_summary=progress_summary,
                             student=current_user)
    except Exception as e:
        flash(f'Error loading progress details: {str(e)}')
        return redirect(url_for('phase_detail', phase_id=phase_id))

@app.route('/api/progress_data/<int:student_id>')
@login_required
def api_progress_data(student_id):
    """API endpoint for progress visualization data"""
    if student_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    if not current_user.is_multi_phase:
        return jsonify({'error': 'Multi-phase project required'}), 400
    
    try:
        # Return basic progress data
        phases = PhaseManager.get_active_phases(student_id)
        progress_data = {
            'phases': [],
            'overall_progress': 0
        }
        
        total_progress = 0
        for phase in phases:
            phase_progress = PhaseManager.get_phase_progress(phase.id)
            progress_data['phases'].append({
                'id': phase.id,
                'name': phase.phase_name,
                'progress': phase_progress['progress_percentage'] if phase_progress else 0
            })
            total_progress += phase_progress['progress_percentage'] if phase_progress else 0
        
        progress_data['overall_progress'] = total_progress / len(phases) if phases else 0
        
        return jsonify(progress_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/update_day_intensity', methods=['POST'])
@login_required
def update_day_intensity():
    date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
    new_intensity = request.form['intensity']
    
    # Update all tasks for this date
    if current_user.is_multi_phase:
        # Use PhaseTask model
        tasks = db.session.query(PhaseTask).join(ProjectPhase).filter(
            ProjectPhase.student_id == current_user.id,
            PhaseTask.date == date
        ).all()
    else:
        # Legacy ScheduleItem model
        tasks = ScheduleItem.query.filter_by(
            student_id=current_user.id,
            date=date
        ).all()
    
    for task in tasks:
        task.day_intensity = new_intensity
        
        # Handle task rescheduling based on new intensity
        if new_intensity == 'none':
            # Move incomplete tasks to next available work day that has capacity
            if not task.completed:
                next_available_slot = find_next_available_slot(current_user, date)
                if next_available_slot:
                    # Get the intensity of the day we're moving to
                    work_day_preferences = json.loads(current_user.work_days) if current_user.work_days else {}
                    target_day_name = next_available_slot.strftime('%A').lower()
                    target_intensity = work_day_preferences.get(target_day_name, 'light')
                    
                    task.date = next_available_slot
                    task.day_intensity = target_intensity
                else:
                    # If no available slots, mark as incomplete but don't reschedule
                    flash(f'Warning: Could not reschedule task "{task.task_description}" - no available slots found.')
    
    db.session.commit()
    
    # If set to none, readjust future schedule to accommodate rescheduled tasks
    if new_intensity == 'none':
        readjust_schedule_from_date(current_user.id, date)
    
    flash(f'Day intensity updated to {new_intensity}. Schedule adjusted accordingly.')
    return redirect(url_for('day_detail', date_str=date.strftime('%Y-%m-%d')))

def find_next_available_slot(student, from_date):
    """Find the next available work day for rescheduling a task"""
    work_day_preferences = json.loads(student.work_days) if student.work_days else {}
    current_date = from_date + timedelta(days=1)
    end_date = student.lit_review_deadline
    
    while current_date <= end_date:
        day_name = current_date.strftime('%A').lower()
        day_intensity = work_day_preferences.get(day_name, 'none')
        
        if day_intensity != 'none':
            # Check how many tasks are already scheduled for this day
            # Handle both PhaseTask and ScheduleItem models
            if student.is_multi_phase:
                existing_tasks_count = PhaseTask.query.join(ProjectPhase).filter(
                    ProjectPhase.student_id == student.id,
                    PhaseTask.date == current_date
                ).count()
            else:
                existing_tasks_count = ScheduleItem.query.filter_by(
                    student_id=student.id,
                    date=current_date
                ).count()
            
            # For rescheduling, we use a more flexible approach
            # Heavy days can handle more tasks than light days
            reasonable_limit = 3 if day_intensity == 'heavy' else 2
            
            # If this day hasn't exceeded reasonable limits, use it
            if existing_tasks_count < reasonable_limit:
                return current_date
        
        current_date += timedelta(days=1)
    
    return None

def readjust_schedule_from_date(student_id, from_date):
    """Intelligently readjust schedule from a specific date forward using new distribution logic"""
    student = Student.query.get(student_id)
    work_day_preferences = json.loads(student.work_days) if student.work_days else {}
    
    # Get all incomplete tasks from this date forward
    if student.is_multi_phase:
        future_tasks = PhaseTask.query.join(ProjectPhase).filter(
            ProjectPhase.student_id == student_id,
            PhaseTask.date >= from_date,
            PhaseTask.completed == False
        ).order_by(PhaseTask.date).all()
        deadline = max([phase.deadline for phase in student.project_phases if phase.is_active])
    else:
        future_tasks = ScheduleItem.query.filter(
            ScheduleItem.student_id == student_id,
            ScheduleItem.date >= from_date,
            ScheduleItem.completed == False
        ).order_by(ScheduleItem.date).all()
        deadline = student.lit_review_deadline
    
    if not future_tasks:
        return
    
    # Get available work days from the from_date to deadline
    available_days = []
    current_date = from_date
    
    while current_date <= deadline:
        day_name = current_date.strftime('%A').lower()
        day_intensity = work_day_preferences.get(day_name, 'none')
        
        if day_intensity != 'none':
            available_days.append({
                'date': current_date,
                'intensity': day_intensity
            })
        
        current_date += timedelta(days=1)
    
    if not available_days:
        flash('Warning: No available work days found for rescheduling.')
        return
    
    # Use the new distribution logic for rescheduling
    task_distribution = PhaseTaskGenerator._calculate_task_distribution(
        len(future_tasks), available_days
    )
    
    # Redistribute tasks based on the new distribution
    task_index = 0
    for day_info in task_distribution:
        tasks_for_day = day_info['task_count']
        
        for _ in range(tasks_for_day):
            if task_index < len(future_tasks):
                task = future_tasks[task_index]
                task.date = day_info['date']
                task.day_intensity = day_info['intensity']
                task_index += 1
    
    db.session.commit()

def generate_schedule(student):
    """Generate initial schedule for the student based on 12-week thesis timeline"""
    work_day_preferences = json.loads(student.work_days) if student.work_days else {}
    current_date = datetime.now().date()
    end_date = student.lit_review_deadline
    
    # Calculate total weeks available
    total_days = (end_date - current_date).days
    total_weeks = max(1, total_days // 7)
    
    # 12-week thesis timeline tasks organized by phase
    weekly_tasks = {
        # Weeks 1-2: Literature Review Foundation
        1: [
            "Create comprehensive list of initial sources from adviser recommendations",
            "Set up note-taking system with template for articles",
            "Begin wide reading to orient toward topic",
            "Start populating reading queue using citation strategies",
            "Begin thesis journal for daily progress and reflections"
        ],
        2: [
            "Skim and take detailed notes on 2 articles per day",
            "Identify research questions and motivations in readings",
            "Begin identifying 2-3 major theoretical frameworks",
            "Organize sources by theme/topic (not chronologically)",
            "Meet with adviser to discuss promising directions"
        ],
        
        # Weeks 3-4: Refining the Research Question
        3: [
            "Continue skimming 2 articles per day",
            "Create literature synopsis extracting key elements",
            "Identify commonalities and literature gaps",
            "Draft 2-3 potential research questions",
            "Practice 3-sentence elevator pitch for project"
        ],
        4: [
            "Finalize specific research question with adviser feedback",
            "Clarify if question is empirical, theoretical, or both",
            "Identify key concepts and variables",
            "Determine sociological significance of question",
            "Draft one-paragraph research gap statement"
        ],
        
        # Weeks 5-6: Methodology Design
        5: [
            "Choose primary research method",
            "Identify validated instruments from literature",
            "Collect examples of similar studies and methods",
            "Draft Methods section outline (sampling, procedure, instruments)",
            "Review methodological blueprints"
        ],
        6: [
            "Draft survey, interview guide, or observation plan",
            "Design backwards from hypothetical results",
            "Calculate sample size and feasibility constraints",
            "Create data collection strategy",
            "Meet with adviser for methods input"
        ],
        
        # Weeks 7-8: Testing and Refinement
        7: [
            "Pilot instruments with 3-5 participants",
            "Refine based on clarity and usefulness",
            "Finalize sampling criteria and recruitment methods",
            "Begin preparing IRB materials",
            "Draft consent forms and recruitment scripts"
        ],
        8: [
            "Conduct second round of pilot testing if needed",
            "Finalize instruments and consent materials",
            "Start writing research proposal introduction",
            "Draft methods section",
            "Create project timeline"
        ],
        
        # Weeks 9-10: IRB and Proposal Draft
        9: [
            "Complete CITI training or ethics certification",
            "Prepare and compile all IRB documents",
            "Finish working draft of research proposal",
            "Synthesize literature review section",
            "Get adviser feedback on IRB documents"
        ],
        10: [
            "Submit IRB application",
            "Complete full draft of research proposal",
            "Include research question, literature review, and methods",
            "Add feasibility and timeline sections",
            "Send to adviser or committee for feedback"
        ],
        
        # Weeks 11-12: Finalization
        11: [
            "Revise proposal based on feedback",
            "Finalize literature review with thematic organization",
            "Ensure methods are consistent with literature",
            "Double-check citation formatting",
            "Identify and justify research gap clearly"
        ],
        12: [
            "Submit final proposal to department/adviser",
            "Check on IRB status and follow up",
            "Plan for next semester recruitment timeline",
            "Set up equipment and materials",
            "Identify remaining literature gaps for future reading"
        ]
    }
    
    # Ongoing weekly tasks to be distributed
    ongoing_tasks = [
        "Skim and note 2 articles per day during deep work time",
        "Review and update literature synopsis",
        "Clean up reading queue and remove irrelevant items",
        "Add exemplary articles to reference file",
        "Maintain thesis journal (20-30 min/day)",
        "Back up work and organize files"
    ]
    
    # Calculate task allocation based on intensity
    current_date = datetime.now().date()
    week_number = 1
    tasks_added = 0
    
    # Create a task queue with all tasks and their weights
    task_queue = []
    for week_num in range(1, min(13, total_weeks + 1)):
        week_tasks = weekly_tasks.get(week_num, [])
        for task in week_tasks:
            task_queue.append({
                'description': f"Week {week_num}: {task}",
                'weight': 2 if any(keyword in task.lower() for keyword in ['draft', 'write', 'create', 'complete']) else 1,
                'week': week_num
            })
    
    # Add ongoing tasks
    for task in ongoing_tasks:
        task_queue.append({
            'description': f"Ongoing: {task}",
            'weight': 1,
            'week': 0
        })
    
    # Distribute tasks based on day intensity
    current_date = datetime.now().date()
    task_index = 0
    
    while current_date <= end_date and task_index < len(task_queue):
        day_name = current_date.strftime('%A').lower()
        day_intensity = work_day_preferences.get(day_name, 'none')
        
        if day_intensity != 'none':
            # Determine how many tasks to assign based on intensity
            if day_intensity == 'heavy':
                tasks_to_assign = 2  # Heavy days get 2x tasks
            else:  # light
                tasks_to_assign = 1
            
            # Assign tasks for this day
            for _ in range(tasks_to_assign):
                if task_index < len(task_queue):
                    task = task_queue[task_index]
                    
                    schedule_item = ScheduleItem(
                        student_id=student.id,
                        date=current_date,
                        task_description=task['description'],
                        day_intensity=day_intensity
                    )
                    db.session.add(schedule_item)
                    task_index += 1
                    tasks_added += 1
        
        current_date += timedelta(days=1)
    
    # If we still have tasks left, cycle through work days again
    while task_index < len(task_queue) and current_date <= end_date:
        day_name = current_date.strftime('%A').lower()
        day_intensity = work_day_preferences.get(day_name, 'none')
        
        if day_intensity != 'none':
            task = task_queue[task_index]
            
            schedule_item = ScheduleItem(
                student_id=student.id,
                date=current_date,
                task_description=task['description'],
                day_intensity=day_intensity
            )
            db.session.add(schedule_item)
            task_index += 1
        
        current_date += timedelta(days=1)
    
    db.session.commit()

def adjust_schedule_if_needed(student_id, date, tasks_completed_count):
    """Adjust schedule based on actual progress"""
    # This function is simplified since we're no longer tracking hours
    # Could be used to adjust future task distribution based on completion patterns
    pass

@app.route('/toggle_task_completion', methods=['POST'])
@login_required
def toggle_task_completion():
    """Toggle task completion status from remaining tasks page"""
    try:
        task_id = request.form.get('task_id')
        is_completed = request.form.get('completed') == 'true'
        
        if not task_id:
            return jsonify({'error': 'Task ID is required'}), 400
        
        # Handle both PhaseTask and ScheduleItem models
        task = None
        if current_user.is_multi_phase:
            task = PhaseTask.query.join(ProjectPhase).filter(
                PhaseTask.id == task_id,
                ProjectPhase.student_id == current_user.id
            ).first()
        else:
            task = ScheduleItem.query.filter_by(
                id=task_id,
                student_id=current_user.id
            ).first()
        
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        task.completed = is_completed
        db.session.commit()
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'completed': is_completed
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/add_task', methods=['POST'])
@login_required
def add_task():
    """Add a new task from remaining tasks page"""
    try:
        task_description = request.form.get('task_description', '').strip()
        task_date = request.form.get('task_date')
        task_intensity = request.form.get('task_intensity', 'light')
        task_priority = request.form.get('task_priority', 'medium')
        phase_id = request.form.get('phase_id', type=int)
        
        if not task_description:
            return jsonify({'error': 'Task description is required'}), 400
        
        if not task_date:
            return jsonify({'error': 'Task date is required'}), 400
        
        try:
            task_date = datetime.strptime(task_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400
        
        # Create new task based on user type
        if current_user.is_multi_phase:
            # Validate phase_id if provided
            if phase_id:
                phase = ProjectPhase.query.filter_by(
                    id=phase_id,
                    student_id=current_user.id,
                    is_active=True
                ).first()
                if not phase:
                    return jsonify({'error': 'Invalid phase selected'}), 400
            else:
                # If no phase specified, use the first active phase
                phase = ProjectPhase.query.filter_by(
                    student_id=current_user.id,
                    is_active=True
                ).order_by(ProjectPhase.order_index).first()
                if phase:
                    phase_id = phase.id
            
            new_task = PhaseTask(
                phase_id=phase_id,
                date=task_date,
                task_description=task_description,
                task_type='general',
                day_intensity=task_intensity,
                priority=task_priority,
                completed=False,
                created_at=datetime.utcnow()
            )
        else:
            new_task = ScheduleItem(
                student_id=current_user.id,
                date=task_date,
                task_description=task_description,
                day_intensity=task_intensity,
                priority=task_priority,
                completed=False,
                created_at=datetime.utcnow()
            )
        
        db.session.add(new_task)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Task added successfully',
            'task_id': new_task.id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/mark_today_complete', methods=['POST'])
@login_required
def mark_today_complete():
    """Mark all of today's tasks as complete"""
    try:
        today = datetime.now().date()
        
        if current_user.is_multi_phase:
            today_tasks = PhaseTask.query.join(ProjectPhase).filter(
                ProjectPhase.student_id == current_user.id,
                PhaseTask.date == today,
                PhaseTask.completed == False
            ).all()
        else:
            today_tasks = ScheduleItem.query.filter_by(
                student_id=current_user.id,
                date=today,
                completed=False
            ).all()
        
        completed_count = 0
        for task in today_tasks:
            task.completed = True
            completed_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Marked {completed_count} tasks as complete',
            'completed_count': completed_count
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Initialize database on startup
def init_db():
    """Initialize database tables and handle migrations"""
    with app.app_context():
        try:
            db.create_all()
            
            # Check if priority column exists, add if missing
            import sqlite3
            db_path = 'instance/paperpacer.db'
            
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Check and add priority column to phase_task if missing
                try:
                    cursor.execute("SELECT priority FROM phase_task LIMIT 1")
                except sqlite3.OperationalError:
                    cursor.execute("ALTER TABLE phase_task ADD COLUMN priority VARCHAR(10) DEFAULT 'medium'")
                    print("Added priority column to phase_task")
                
                # Check and add priority column to schedule_item if missing
                try:
                    cursor.execute("SELECT priority FROM schedule_item LIMIT 1")
                except sqlite3.OperationalError:
                    cursor.execute("ALTER TABLE schedule_item ADD COLUMN priority VARCHAR(10) DEFAULT 'medium'")
                    print("Added priority column to schedule_item")
                
                conn.commit()
                conn.close()
            
            print("Database initialized successfully!")
            
        except Exception as e:
            print(f"Database initialization error: {e}")

# Initialize database on import
init_db()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")
    app.run(debug=True)
