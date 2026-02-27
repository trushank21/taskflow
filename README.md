# TaskManager - Professional Task Management System

A professional task management system built with Django, Bootstrap 5, and MySQL - similar to ClickUp, designed for companies to assign and track tasks efficiently.

## Features

### 1. **User Management & Authentication**
- Role-based access control (Admin, Manager, Developer)
- User profiles with department and role assignment
- Secure login/logout system
- Admin panel for user management

### 2. **Project Management**
- Create and manage projects
- Assign team members to projects
- Set project status (Active, Inactive, Completed, On Hold)
- Track project progress
- Define team leads for each project

### 3. **Task Management**
- Create tasks within projects
- Assign tasks to specific team members
- **Task Status**: To Do, In Progress, In Review, Completed, Blocked
- **Task Priority**: Low, Medium, High, Urgent
- Track task progress (0-100%)
- Estimate and track actual hours spent
- Set due dates with reminders
- Add tags to tasks for better organization

### 4. **Collaboration Features**
- Add comments to tasks
- Attach files to tasks
- Real-time task updates
- Task history tracking

### 5. **Filtering & Search**
- Filter tasks by:
  - Status
  - Priority
  - Project
  - Assigned user
  - Due date range
  - Title/description search
- Quick search functionality
- Saved filters for quick access

### 6. **Dashboard**
- Task statistics (Total, To Do, In Progress, Completed)
- Urgent tasks overview
- Recent tasks display
- Quick action buttons
- Visual progress indicators

### 7. **Professional UI/UX**
- Responsive design (works on desktop, tablet, mobile)
- Modern color scheme with gradients
- Interactive components with hover effects
- Bootstrap 5 framework
- Font Awesome icons
- Clean and intuitive navigation

## Project Structure

```
taskmanager/
├── config/                 # Django project configuration
│   ├── settings.py        # Project settings
│   ├── urls.py           # Main URL configuration
│   ├── wsgi.py           # WSGI configuration
│   └── __init__.py
├── accounts/             # User management app
│   ├── models.py         # UserProfile model
│   ├── views.py          # Views logic
│   ├── admin.py          # Admin configurations
│   ├── urls.py           # Account URL routes
│   └── migrations/       # Database migrations
├── projects/            # Project management app
│   ├── models.py        # Project model
│   ├── views.py         # Project views
│   ├── forms.py         # Project forms
│   ├── admin.py         # Project admin
│   ├── urls.py          # Project URL routes
│   └── migrations/
├── tasks/              # Task management app
│   ├── models.py       # Task, TaskComment, TaskAttachment models
│   ├── views.py        # Task views and logic
│   ├── forms.py        # Task forms
│   ├── filters.py      # Task filtering
│   ├── admin.py        # Task admin
│   ├── urls.py         # Task URL routes
│   └── migrations/
├── templates/          # HTML templates
│   ├── base.html       # Base template with navbar and sidebar
│   ├── accounts/       # Account templates
│   ├── tasks/          # Task templates
│   └── projects/       # Project templates
├── static/            # Static files
│   ├── css/           # Custom CSS
│   ├── js/            # Custom JavaScript
│   └── images/        # Images
├── manage.py          # Django management script
├── db.sqlite3         # Database (SQLite for development)
└── venv/              # Virtual environment
```

## Database Models

### UserProfile
- Extended Django User model
- Role: Admin, Manager, Developer
- Department, Phone, Bio, Avatar

### Project
- Title, Description, Status
- Created by, Team Lead
- Team Members (Many-to-Many)
- Start/End dates with timestamps

### Task
- Title, Description
- Project (FK), Assigned To (FK), Assigned By (FK)
- Status, Priority
- Progress (0-100%), Due Date
- Estimated/Actual Hours
- Tags for categorization

### TaskComment
- Task (FK), Commented By (FK)
- Comment text with timestamps

### TaskAttachment
- Task (FK), Uploaded By (FK)
- File storage with file name

## Installation & Setup

### 1. **Clone or Extract Project**
```bash
cd c:\Users\HP\Desktop\Django\taskmanager
```

### 2. **Activate Virtual Environment**
```bash
# Windows PowerShell
.\venv\Scripts\Activate.ps1

# Windows CMD
.\venv\Scripts\activate.bat
```

### 3. **Install Dependencies** (Already done)
```bash
pip install django==4.2 django-filter python-dotenv pillow
```

### 4. **Run Migrations** (Already done)
```bash
python manage.py migrate
```

### 5. **Create Superuser** (Already done)
Demo credentials:
- Username: `admin`
- Password: `admin@123`

### 6. **Start Development Server**
```bash
python manage.py runserver
```

Visit: `http://localhost:8000`

## Usage Guide

### Login
1. Open http://localhost:8000
2. Use demo credentials:
   - Username: `admin`
   - Password: `admin@123`

### Dashboard
- View task statistics
- See urgent tasks
- Access recent tasks
- Quick action buttons

### Create a Project
1. Click **Projects** in sidebar
2. Click **New Project** button
3. Fill in project details
4. Assign team members
5. Set dates and status

### Create a Task
1. Click **My Tasks** in sidebar
2. Click **New Task** button
3. Select project and assignee
4. Set priority and due date
5. Estimate hours

### Filter Tasks
1. Go to **My Tasks**
2. Use filter options:
   - Search by title
   - Filter by status
   - Filter by priority
   - Filter by project
   - Filter by assignee

### Manage Tasks
- View task details and comments
- Update task status
- Add comments for collaboration
- Attach files
- Track progress
- Update estimated/actual hours

### Admin Panel
1. Click **Admin Panel** (Admin/Manager only)
2. Manage Users, Projects, Tasks
3. View system statistics
4. Configure settings

## Key Features Implementation

### 1. **Authentication**
- Django built-in auth system
- Login required mixins on views
- Role-based access control

### 2. **Filtering System**
```python
# Using django-filter for advanced filtering
class TaskFilter(django_filters.FilterSet):
    # Multiple filter options
    title = CharField (icontains lookup)
    status = ChoiceFilter
    priority = ChoiceFilter
    # Date range filtering
```

### 3. **Professional UI**
- Bootstrap 5 grid system
- Responsive navigation bar
- Collapsible sidebar
- Color-coded badges for status/priority
- Progress indicators
- Card-based layouts

### 4. **CRUD Operations**
- Create: TaskCreateView
- Read: TaskDetailView, TaskListView
- Update: TaskUpdateView
- Delete: TaskDeleteView

## Customization

### Change Database to MySQL
In `config/settings.py`:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'taskmanager',
        'USER': 'root',
        'PASSWORD': 'your_password',
        'HOST': '127.0.0.1',
        'PORT': '3306',
    }
}
```

### Add New Fields to Task
1. Edit `tasks/models.py`
2. Add field to Task model
3. Run `python manage.py makemigrations`
4. Run `python manage.py migrate`

### Customize Colors
Edit `templates/base.html` CSS variables:
```css
:root {
    --primary-color: #6366f1;
    --secondary-color: #4f46e5;
    /* ... other colors ... */
}
```

### Add New User Role
1. Edit UserProfile model choices
2. Add role-based views/decorators
3. Apply permissions

## Production Deployment

### 1. Update Settings
- Set `DEBUG = False` in settings.py
- Update `ALLOWED_HOSTS`
- Use environment variables for secrets

### 2. Collect Static Files
```bash
python manage.py collectstatic
```

### 3. Use Production Database
- Switch to MySQL or PostgreSQL
- Set up proper backups

### 4. Use WSGI Server
```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

### 5. Set Up Reverse Proxy
- Use Nginx or Apache
- Configure SSL/TLS certificates

## Troubleshooting

### Login Issues
- Ensure database migrations are applied
- Check superuser exists: `python manage.py createsuperuser`
- Verify settings.py LOGIN_URL and LOGIN_REDIRECT_URL

### Static Files Not Loading
- Run `python manage.py collectstatic`
- Check STATIC_URL and STATIC_ROOT in settings.py

### Database Connection Issues
- Verify database credentials in .env
- Ensure MySQL server is running
- Check character encoding (utf8mb4)

### Permission Denied
- Check user role in admin panel
- Verify user is part of project team
- Check view mixins and decorators

## Future Enhancements

- Real-time notifications
- Email reminders for due tasks
- Task templates
- Time tracking with timer
- Kanban board view
- Gantt chart view
- Advanced reporting
- Integration with Slack/Teams
- Mobile app
- Export to PDF/Excel

## API Documentation

Future REST API endpoints will include:
- `/api/tasks/` - List and create tasks
- `/api/tasks/<id>/` - Get, update, delete task
- `/api/projects/` - Project endpoints
- `/api/comments/` - Comment endpoints

## Support & Contributing

For issues or suggestions, please create an issue in the project repository.

## License

This project is built for internal company use. Custom modifications welcomed.

---

**Created:** February 17, 2026  
**Tech Stack:** Django 4.2, Bootstrap 5, SQLite/MySQL, jQuery  
**Status:** Development Ready ✅
#   t a s k f l o w  
 