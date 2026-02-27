# TaskManager - Developer Documentation

## Architecture Overview

### Technology Stack
- **Backend**: Django 4.2 (Python Web Framework)
- **Database**: SQLite (Development) / MySQL (Production)
- **Frontend**: HTML5, Bootstrap 5, jQuery, CSS3
- **Libraries**: django-filter, Pillow, python-dotenv

### Project Architecture

```
MVC (Model-View-Controller) + MTV (Model-Template-View)

Models (Database Layer)
    ↓
Views (Business Logic)
    ↓
Templates (Presentation)
```

---

## Models Architecture

### UserProfile Model
```python
class UserProfile(models.Model):
    - Extends Django's built-in User model
    - Role-based access control
    - Department and personal information
    - Relations: OneToOne with User
```

### Project Model
```python
class Project(models.Model):
    - Container for tasks
    - Team assignment and management
    - Status tracking
    - Start and end dates
    - Relations: FK to User (created_by, team_lead)
            : M2M to User (team_members)
```

### Task Model
```python
class Task(models.Model):
    - Main task entity
    - Status and priority fields
    - Assignment to users
    - Progress tracking (0-100%)
    - Time estimation and tracking
    - Relations: FK to Project
            : FK to User (assigned_to, assigned_by)
```

### TaskComment Model
```python
class TaskComment(models.Model):
    - Collaboration feature
    - Comment history with timestamps
    - Relations: FK to Task
            : FK to User (commented_by)
```

### TaskAttachment Model
```python
class TaskAttachment(models.Model):
    - File attachment support
    - File upload to media/task_attachments/
    - Relations: FK to Task
            : FK to User (uploaded_by)
```

---

## Views & URL Routing

### Task Views Hierarchy

```
TaskListView (FilterView)
├── get_queryset() - Role-based filtering
├── Filters applied via TaskFilter
└── Context: tasks, filters

TaskDetailView (DetailView)
├── Additional context: comments, attachments
└── Related data from TaskComment, TaskAttachment

TaskCreateView (CreateView)
├── Pre-fills assigned_by with request.user
└── Success URL: task_detail

TaskUpdateView (UpdateView)
├── Updates existing task
└── Success URL: task_detail

TaskDeleteView (DeleteView)
├── Soft/hard delete handling
└── Success URL: task_list
```

### Project Views Hierarchy

```
ProjectListView (ListView)
├── Role-based queryset filtering
└── Prefetch team_members data

ProjectDetailView (DetailView)
├── Includes related tasks
├── Task count statistics
└── Task breakdown by status

ProjectCreateView (CreateView)
├── Auto-assigns created_by
└── Store team assignments

ProjectUpdateView (UpdateView)
ProjectDeleteView (DeleteView)
```

---

## Filter System

### TaskFilter Implementation

```python
TaskFilter class (django_filters.FilterSet):

1. Title Filter
   - Type: CharFilter
   - Lookup: icontains (case-insensitive)
   - Widget: TextInput with placeholder

2. Project Filter
   - Type: ModelChoiceFilter
   - Queryset: All projects
   - Empty label: "All Projects"

3. Status Filter
   - Type: ChoiceFilter
   - Choices: Task.STATUS_CHOICES
   - Options: todo, in_progress, in_review, completed, blocked

4. Priority Filter
   - Type: ChoiceFilter
   - Choices: Task.PRIORITY_CHOICES
   - Options: low, medium, high, urgent

5. Assigned To Filter
   - Type: ModelChoiceFilter
   - Queryset: Developers only
   - Display: Full name or username

6. Due Date Range
   - Type: DateFromToRangeFilter
   - Range: from_date to to_date
```

### Filter Flow

```
Request with query parameters
    ↓
FilterView.get_queryset()
    ↓
Apply filters from TaskFilter
    ↓
Return filtered queryset
    ↓
Render template with filtered data
```

---

## Template Structure

### Base Template (base.html)
- Navigation bar with gradient
- Responsive sidebar with navigation
- Main content area
- CSS variables for theming
- Bootstrap grid system

### Dashboard Template
- Statistics cards (4 columns)
- Urgent tasks list
- Recent tasks list
- Quick action buttons

### Task List Template
- Filter sidebar
- Table/card view of tasks
- Badges for status/priority
- Progress bars
- Pagination

### Task Detail Template
- Task information display
- Comments section
- File attachments area
- Status update controls
- Edit/delete buttons

### Project List Template
- Project cards (grid view)
- Team member display
- Progress indicators
- Quick actions

---

## URL Routing Map

```
/ (root)
├── Login: /login/
├── Logout: /logout/
└── Dashboard: / [task_view]

/tasks/
├── List: /tasks/ [FilterView]
├── Create: /tasks/create/ [CreateView]
├── Detail: /tasks/<id>/ [DetailView]
├── Edit: /tasks/<id>/edit/ [UpdateView]
├── Delete: /tasks/<id>/delete/ [DeleteView]
├── Comment: /tasks/<id>/comment/ [POST]
└── Status: /tasks/<id>/status/ [POST]

/projects/
├── List: /projects/ [ListView]
├── Create: /projects/create/ [CreateView]
├── Detail: /projects/<id>/ [DetailView]
├── Edit: /projects/<id>/edit/ [UpdateView]
└── Delete: /projects/<id>/delete/ [DeleteView]

/accounts/
└── Profile: /accounts/profile/ [profile_view]

/admin/
└── Admin Panel [Django admin]
```

---

## Security & Permissions

### Authentication
- `@login_required` decorator on views
- `LoginRequiredMixin` on class-based views
- Login URL: `/login/`
- Session-based authentication

### Authorization (Role-Based)
```python
# Admin: Full access to all views
# Manager: Can create projects, assign tasks
# Developer: Can only view and update assigned tasks

# Check in views:
if user.profile.role == 'admin':
    # Full access
```

### CSRF Protection
- `{% csrf_token %}` in all forms
- Django middleware handles validation

### Data Privacy
- Users see only their assigned tasks (except admin/manager)
- Comments and attachments scoped to task
- No direct access to other user's data

---

## Forms Implementation

### TaskForm (ModelForm)
```python
Fields: title, description, project, assigned_to, status,
        priority, due_date, estimated_hours, tags

Widgets: TextInput, Textarea, Select, DateTimeInput, NumberInput
Styling: All inputs have form-control class
```

### TaskCommentForm
```python
Fields: comment (Textarea only)
Styling: Bootstrap form styling
```

### ProjectForm
```python
Fields: title, description, status, team_lead, team_members,
        start_date, end_date

Widgets: Many-to-Many select for team_members
Styling: Bootstrap form styling
```

---

## Database Indexing

### Performance Optimization

```python
# Task model indexes
- status (most common filter)
- priority (sorting/filtering)
- assigned_to (user's tasks)
- project (project view)

# Queryset optimization
- select_related() for FK
- prefetch_related() for M2M
- Only query needed fields
```

---

## Static Files & Media

### Directory Structure
```
static/
├── css/
│   └── custom.css (future custom styles)
├── js/
│   └── custom.js (future custom scripts)
└── images/
    └── (future images/icons)

media/
├── avatars/
│   └── user_profile_images
├── task_attachments/
│   └── uploaded_files
```

### Bootstrap & CDN
- Bootstrap 5 CSS: CDN link (no download needed)
- Font Awesome icons: CDN link
- jQuery: CDN link
- Google Fonts: CDN (Poppins font)

---

## Adding New Features

### Add a New Field to Task

1. **Edit Model** (`tasks/models.py`)
```python
class Task(models.Model):
    # Add new field
    custom_field = models.CharField(max_length=100, blank=True)
```

2. **Create Migration**
```bash
python manage.py makemigrations
```

3. **Apply Migration**
```bash
python manage.py migrate
```

4. **Update Form** (`tasks/forms.py`)
```python
class TaskForm(ModelForm):
    fields = [..., 'custom_field']  # Add to list
```

5. **Update Template** (`tasks/task_form.html`)
```html
{{ form.custom_field }}
```

6. **Update Admin** (`tasks/admin.py`)
```python
fieldsets = (
    ('Task Info', {'fields': ('title', ..., 'custom_field')}),
    ...
)
```

### Add a New View

1. **Create View** (`tasks/views.py`)
```python
class CustomView(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'tasks/custom.html'
```

2. **Update URLs** (`tasks/urls.py`)
```python
urlpatterns = [
    path('custom/', views.CustomView.as_view(), name='custom'),
]
```

3. **Create Template** (`templates/tasks/custom.html`)
```html
{% extends 'base.html' %}
{% block content %}
<!-- Your content -->
{% endblock %}
```

### Add a New Role

1. **Update UserProfile Model**
```python
ROLE_CHOICES = (
    ...
    ('custom_role', 'Custom Role'),
)
```

2. **Create Permission Decorator**
```python
def custom_role_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.profile.role == 'custom_role':
            return view_func(request, *args, **kwargs)
        raise PermissionDenied()
    return wrapper
```

3. **Apply to Views**
```python
@custom_role_required
def custom_view(request):
    ...
```

---

## Performance Considerations

### Query Optimization

**Bad:**
```python
tasks = Task.objects.all()
for task in tasks:
    print(task.project.title)  # N+1 query problem
    print(task.assigned_to.username)
```

**Good:**
```python
tasks = Task.objects.select_related('project', 'assigned_to')
for task in tasks:
    print(task.project.title)  # No additional queries
```

### Caching Strategy
```python
# Cache filter choices
@cache_page(60 * 60)  # Cache for 1 hour
def expensive_view(request):
    ...
```

### Database Indexing
- Already added for task filtering
- Consider adding for frequently sorted fields
- Monitor with Django Debug Toolbar

---

## Testing Strategy (Future)

### Unit Tests
```python
# tests/test_models.py
class TaskModelTest(TestCase):
    def test_task_creation(self):
        task = Task.objects.create(...)
        self.assertEqual(task.title, 'Test')
```

### View Tests
```python
# tests/test_views.py
class TaskListViewTest(TestCase):
    def test_task_list_access(self):
        response = self.client.get('/tasks/')
        self.assertEqual(response.status_code, 200)
```

### Integration Tests
```python
# Test full workflow
```

---

## Deployment Checklist

- [ ] Set DEBUG = False
- [ ] Collect static files
- [ ] Set ALLOWED_HOSTS
- [ ] Configure database (MySQL)
- [ ] Set SECRET_KEY via environment
- [ ] Enable HTTPS
- [ ] Set up logging
- [ ] Configure email backend
- [ ] Set up backups
- [ ] Configure monitoring
- [ ] Use WSGI server (Gunicorn)

---

## Common Errors & Solutions

### ImproperlyConfigured: "mysqlclient 2.2.1 or newer is required"
**Solution**: Use PyMySQL instead
```python
# config/__init__.py
import pymysql
pymysql.install_as_MySQLdb()
```

### TemplateDoesNotExist
**Solution**: Check TEMPLATES dirs in settings
```python
'DIRS': [BASE_DIR / 'templates'],
```

### StaticFilesNotFound in Production
**Solution**: Run collectstatic
```bash
python manage.py collectstatic
```

### Permission Denied on View
**Solution**: Check user role and decorators
```python
@login_required
@permission_required('app.can_view')
```

---

## API Development (Future)

### DRF Integration
```bash
pip install djangorestframework
```

### Serializers
```python
class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'
```

### ViewSets & URLs
```python
router = DefaultRouter()
router.register(r'tasks', TaskViewSet)
```

---

## Additional Resources

- Django Documentation: https://docs.djangoproject.com/
- Bootstrap Documentation: https://getbootstrap.com/docs/
- django-filter: https://django-filter.readthedocs.io/
- jQuery: https://jquery.com/
- Font Awesome: https://fontawesome.com/

---

**Built for developers, by developers**  
*Happy coding! 🚀*
