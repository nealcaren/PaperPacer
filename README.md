# 📚 PaperPacer

A comprehensive web application that helps students manage their senior honors thesis journey through intelligent scheduling, progress tracking, and task management. From literature reviews to IRB proposals, PaperPacer guides students through every aspect of academic research.

## ✨ Current Features

### 🎯 **Core Functionality**
- **Smart Onboarding**: Collects project details, deadlines, and personalized work preferences
- **Intelligent Scheduling**: Generates 12-week academic timeline with task intensity management
- **Interactive Calendar**: Visual calendar view with color-coded workload indicators
- **Progress Tracking**: Daily check-ins with toggle switches for task completion
- **Catch-Up Mode**: Ability to mark tasks complete for past dates
- **Comprehensive Task View**: See all remaining work organized by priority

### 👤 **User Management**
- **User Authentication**: Secure registration and login system
- **Password Reset**: Email-based password recovery with secure tokens
- **Personalized Dashboards**: Individual progress tracking and statistics
- **Flexible Scheduling**: Light/Heavy day intensity with dropdown selectors

### 🎨 **Modern Interface**
- **Responsive Design**: Mobile-first approach with CSS Grid and Flexbox
- **Toggle Switches**: Modern UI for task completion (replacing checkboxes)
- **Dropdown Menus**: Clean interface for multi-option selections
- **Interactive Calendar**: Clickable dates with detailed day views
- **Real-time Feedback**: Dynamic visual updates and progress indicators

## 🚀 Quick Start

### Prerequisites

- **Python 3.7+** 
- **pip** (Python package installer)

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd paper-pacer-prep
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize the database**:
   ```bash
   python init_db.py
   ```

4. **Configure email** (optional - see [EMAIL_SETUP.md](EMAIL_SETUP.md)):
   ```bash
   cp .env.example .env
   # Edit .env with your email settings
   ```

### Running the Application

1. **Start the server**:
   ```bash
   python app.py
   ```

2. **Open your browser**:
   ```
   http://localhost:5000
   ```

3. **Create an account** and complete the onboarding process

## 🎯 How It Works

### 1. **Smart Onboarding**
Students create their personalized workspace:
- **Account Creation**: Secure registration with email verification
- **Project Setup**: Thesis title and literature review deadline  
- **Work Preferences**: Day intensity levels (None/Light/Heavy) with dropdown selection
- **Schedule Generation**: Automatic 12-week academic timeline creation

### 2. **Intelligent Task Management**
The system generates research-focused tasks:
- **Literature Foundation**: Source identification and academic database searches
- **Deep Reading**: Systematic note-taking and thematic organization
- **Research Development**: Question formulation and theoretical framework building
- **Academic Writing**: Draft preparation and revision cycles
- **Progress Tracking**: Real-time completion monitoring with visual feedback

### 3. **Interactive Progress Tracking**
Modern interface for daily engagement:
- **Toggle Switches**: Intuitive task completion with visual feedback
- **Calendar View**: Color-coded workload visualization across weeks
- **Catch-Up Mode**: Flexible completion tracking for missed days
- **Notes System**: Contextual progress documentation

### 4. **Adaptive Scheduling Intelligence**
Dynamic schedule management:
- **Capacity Respect**: Smart rescheduling that honors day intensity limits
- **Deadline Awareness**: Automatic task redistribution based on remaining time
- **Completion Patterns**: Learning from actual vs. planned progress
- **Workload Balancing**: Optimal task distribution across available work days

## 📁 Project Structure

```
paper-pacer-prep/
├── app.py                    # Main Flask application with routes and models
├── config.py                 # Configuration management for different environments
├── init_db.py               # Database initialization and schema updates
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
├── EMAIL_SETUP.md          # Comprehensive email configuration guide
├── templates/              # Jinja2 HTML templates
│   ├── base.html           # Base template with modern CSS and components
│   ├── index.html          # Welcome/landing page
│   ├── register.html       # User registration form
│   ├── login.html          # User login with password reset link
│   ├── forgot_password.html # Password reset request form
│   ├── reset_password.html  # Secure password reset form
│   ├── onboard.html        # Project onboarding with dropdown selectors
│   ├── dashboard.html      # Main dashboard with interactive calendar
│   ├── daily_checkin.html  # Daily progress with toggle switches
│   ├── day_detail.html     # Individual day management interface
│   ├── remaining_tasks.html # Comprehensive task overview
│   └── settings.html       # User settings and preferences
└── paperpacer.db           # SQLite database (auto-created)
```

## 🗄️ Database Schema

### **Student Model** (User accounts with authentication)
- Authentication: `id`, `name`, `email`, `password_hash`
- Project: `project_title`, `thesis_deadline`, `lit_review_deadline`
- Preferences: `work_days` (JSON), `onboarded`, `created_at`
- Security: `reset_token`, `reset_token_expires`

### **ScheduleItem Model** (Individual tasks and scheduling)
- Task: `id`, `student_id`, `date`, `task_description`
- Management: `day_intensity`, `completed`, `created_at`

### **ProgressLog Model** (Daily progress tracking)
- Progress: `id`, `student_id`, `date`, `tasks_completed` (JSON)
- Documentation: `notes`, `created_at`

## 🛠️ Technology Stack

### **Backend**
- **Flask**: Python web framework with SQLAlchemy ORM
- **SQLite**: Lightweight database with automatic schema management  
- **Flask-Login**: Session management and user authentication
- **Email Integration**: SMTP support for password reset functionality

### **Frontend**
- **Modern CSS**: CSS Variables, Grid, Flexbox with Inter font
- **Responsive Design**: Mobile-first approach with breakpoints
- **Interactive Components**: Toggle switches, dropdown menus, dynamic calendar
- **JavaScript**: ES6+ for calendar navigation and real-time UI updates

## 🚀 Roadmap: Next Development Stages

### **Phase 2: Multi-Project Architecture** 🎯
Transform PaperPacer from single-project to comprehensive research management platform.

#### **2.1 Multi-Project Support**
- **Project Management Dashboard**: Central hub showing all active projects
- **Project Creation Wizard**: Quick setup for new research projects
- **Project Switching**: Seamless context switching between different theses/papers
- **Project Templates**: Pre-configured setups for different research types
- **Project Archiving**: Complete and archive finished projects

#### **2.2 Enhanced Database Schema**
```sql
-- New Models for Multi-Project Support
Project: id, student_id, title, type, status, created_at, archived_at
ProjectPhase: id, project_id, phase_type, deadline, priority, status
ProjectTask: id, project_phase_id, description, date, completed
```

### **Phase 3: Multi-Aspect Project Management** 📋
Restructure onboarding and scheduling around distinct project phases.

#### **3.1 Project Phases System**
Replace single literature review focus with comprehensive research phases:

**📚 Literature Review Phase**
- Systematic literature searches
- Source evaluation and note-taking
- Thematic analysis and synthesis
- Literature gap identification

**❓ Research Question Development**
- Problem statement formulation
- Research question refinement
- Hypothesis development
- Theoretical framework selection

**🔬 Methods Planning Phase**
- Research design selection
- Methodology documentation
- Data collection planning
- Analysis strategy development

**📋 IRB Proposal Phase**
- Ethics application preparation
- Consent form development
- Risk assessment documentation
- IRB submission and revisions

#### **3.2 Smart Onboarding Redesign**
**Current Flow**: Single deadline → Generated schedule
**New Flow**: Multiple phases → Individual deadlines → Integrated timeline

```
New Onboarding Process:
1. Project Overview (title, type, final deadline)
2. Phase Selection & Deadlines
   ├── Literature Review: [deadline picker]
   ├── Research Question: [deadline picker] 
   ├── Methods Plan: [deadline picker]
   └── IRB Proposal: [deadline picker]
3. Work Preferences (same as current)
4. Integrated Schedule Generation
```

#### **3.3 Phase-Aware Task Generation**
- **Literature Review Tasks**: Current 12-week timeline system
- **Research Question Tasks**: Iterative refinement and advisor feedback cycles
- **Methods Tasks**: Research design templates and validation checklists
- **IRB Tasks**: Compliance requirements and documentation workflows

### **Phase 4: Advanced Features** ⚡

#### **4.1 Smart Dependencies**
- **Phase Prerequisites**: Literature review completion unlocks research question refinement
- **Flexible Timelines**: Automatic schedule adjustment based on phase completion
- **Critical Path Analysis**: Identify and highlight schedule bottlenecks

#### **4.2 Collaboration Features**
- **Advisor Integration**: Share progress and receive feedback
- **Peer Collaboration**: Study groups and peer review systems
- **Committee Management**: Multiple advisor/committee member access

#### **4.3 Advanced Analytics**
- **Progress Predictions**: Machine learning for completion forecasting
- **Productivity Insights**: Personal work pattern analysis
- **Comparative Benchmarks**: Anonymous peer comparison data

### **Phase 5: Integration & Polish** 🎨

#### **5.1 External Integrations**
- **Reference Managers**: Zotero, Mendeley, EndNote sync
- **Writing Tools**: LaTeX, Word, Google Docs integration
- **Calendar Sync**: Google Calendar, Outlook integration
- **File Storage**: Google Drive, Dropbox, OneDrive connectivity

#### **5.2 Mobile & Accessibility**
- **Progressive Web App**: Offline capability and mobile optimization
- **Accessibility Compliance**: WCAG 2.1 AA standard implementation
- **Multi-language Support**: Internationalization framework

## 🎯 Implementation Priorities

### **Immediate Next Steps** (Phase 2)
1. **Database Migration**: Add Project model and relationships
2. **Multi-Project UI**: Project selection and management interface
3. **Project Dashboard**: Overview of all active projects
4. **Migration Tools**: Convert existing single-project users

### **Short-term Goals** (Phase 3)  
1. **Phase System**: Implement the four core research phases
2. **Enhanced Onboarding**: Multi-deadline project setup
3. **Phase-Specific Tasks**: Customized task generation per phase
4. **Integrated Timeline**: Cross-phase schedule coordination

### **Long-term Vision** (Phases 4-5)
1. **Advanced Analytics**: Predictive scheduling and insights
2. **Collaboration Platform**: Multi-user research management
3. **Integration Ecosystem**: Connect with existing academic tools
4. **Mobile Experience**: Full-featured mobile application

---

*This roadmap transforms PaperPacer from a literature review tool into a comprehensive thesis and research project management platform, supporting students throughout their entire academic research journey.*