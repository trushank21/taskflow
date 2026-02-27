import os
import django
from datetime import datetime, timedelta
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import UserProfile
from projects.models import Project
from tasks.models import Task

print("=" * 60)
print("TaskManager - Demo Data Setup")
print("=" * 60)

# Clear existing test data (optional - comment out if you want to keep)
# User.objects.filter(username__startswith='test_').delete()

# ============ Create Users ============
print("\n📝 Creating test users...")

users_data = [
    {'username': 'john_dev', 'email': 'john@company.com', 'first_name': 'John', 'last_name': 'Developer', 'role': 'developer'},
    {'username': 'sarah_dev', 'email': 'sarah@company.com', 'first_name': 'Sarah', 'last_name': 'Developer', 'role': 'developer'},
    {'username': 'mike_manager', 'email': 'mike@company.com', 'first_name': 'Mike', 'last_name': 'Manager', 'role': 'manager'},
    {'username': 'lisa_manager', 'email': 'lisa@company.com', 'first_name': 'Lisa', 'last_name': 'Manager', 'role': 'manager'},
]

created_users = {}
admin_user = User.objects.get(username='admin')

for user_data in users_data:
    username = user_data['username']
    if not User.objects.filter(username=username).exists():
        user = User.objects.create_user(
            username=username,
            email=user_data['email'],
            password='test@123',
            first_name=user_data['first_name'],
            last_name=user_data['last_name']
        )
        UserProfile.objects.create(user=user, role=user_data['role'], department='Engineering')
        created_users[username] = user
        print(f"  ✅ Created user: {username} ({user_data['role']})")
    else:
        created_users[username] = User.objects.get(username=username)
        print(f"  ℹ️  User already exists: {username}")

# ============ Create Projects ============
print("\n📁 Creating projects...")

projects_data = [
    {
        'title': 'Website Redesign',
        'description': 'Complete redesign of the company website with modern UI/UX',
        'status': 'active',
        'team_lead': 'mike_manager',
        'team_members': ['john_dev', 'sarah_dev'],
    },
    {
        'title': 'Mobile App Development',
        'description': 'Build a cross-platform mobile application',
        'status': 'active',
        'team_lead': 'lisa_manager',
        'team_members': ['john_dev', 'sarah_dev'],
    },
    {
        'title': 'Database Migration',
        'description': 'Migrate from legacy database to modern cloud infrastructure',
        'status': 'in_progress',
        'team_lead': 'mike_manager',
        'team_members': ['sarah_dev'],
    },
]

created_projects = {}
today = datetime.now().date()

for project_data in projects_data:
    try:
        project = Project.objects.create(
            title=project_data['title'],
            description=project_data['description'],
            status=project_data['status'],
            created_by=admin_user,
            team_lead=created_users.get(project_data['team_lead']),
            start_date=today,
            end_date=today + timedelta(days=60)
        )
        
        # Add team members
        for member_username in project_data['team_members']:
            project.team_members.add(created_users[member_username])
        
        created_projects[project_data['title']] = project
        print(f"  ✅ Created project: {project_data['title']}")
    except Exception as e:
        print(f"  ❌ Error creating project {project_data['title']}: {e}")

# ============ Create Tasks ============
print("\n✅ Creating tasks...")

tasks_data = [
    # Website Redesign tasks
    {
        'title': 'Design Homepage Layout',
        'description': 'Create wireframes and design mockups for the homepage',
        'project': 'Website Redesign',
        'assigned_to': 'john_dev',
        'status': 'in_progress',
        'priority': 'high',
        'progress': 65,
        'due_days': 7,
    },
    {
        'title': 'Implement Homepage HTML/CSS',
        'description': 'Convert design mockups to responsive HTML/CSS',
        'project': 'Website Redesign',
        'assigned_to': 'sarah_dev',
        'status': 'todo',
        'priority': 'high',
        'progress': 0,
        'due_days': 14,
    },
    {
        'title': 'Create About Us Page',
        'description': 'Design and implement the About Us page',
        'project': 'Website Redesign',
        'assigned_to': 'john_dev',
        'status': 'todo',
        'priority': 'medium',
        'progress': 0,
        'due_days': 21,
    },
    {
        'title': 'Setup Contact Form',
        'description': 'Design and implement contact form with validation',
        'project': 'Website Redesign',
        'assigned_to': 'sarah_dev',
        'status': 'blocked',
        'priority': 'medium',
        'progress': 30,
        'due_days': 10,
    },
    
    # Mobile App tasks
    {
        'title': 'Design App UI/UX',
        'description': 'Create comprehensive UI/UX design for mobile app',
        'project': 'Mobile App Development',
        'assigned_to': 'sarah_dev',
        'status': 'in_review',
        'priority': 'urgent',
        'progress': 85,
        'due_days': 3,
    },
    {
        'title': 'Setup Development Environment',
        'description': 'Setup React Native dev environment and project structure',
        'project': 'Mobile App Development',
        'assigned_to': 'john_dev',
        'status': 'completed',
        'priority': 'high',
        'progress': 100,
        'due_days': 2,
    },
    {
        'title': 'Implement Authentication',
        'description': 'Implement user authentication and security',
        'project': 'Mobile App Development',
        'assigned_to': 'john_dev',
        'status': 'todo',
        'priority': 'high',
        'progress': 0,
        'due_days': 21,
    },
    {
        'title': 'Create User Dashboard',
        'description': 'Build main dashboard screen with user data',
        'project': 'Mobile App Development',
        'assigned_to': 'sarah_dev',
        'status': 'todo',
        'priority': 'medium',
        'progress': 0,
        'due_days': 28,
    },
    
    # Database Migration tasks
    {
        'title': 'Analyze Current Database',
        'description': 'Document current schema and data structure',
        'project': 'Database Migration',
        'assigned_to': 'sarah_dev',
        'status': 'completed',
        'priority': 'high',
        'progress': 100,
        'due_days': 1,
    },
    {
        'title': 'Design New Database Schema',
        'description': 'Design optimized schema for cloud infrastructure',
        'project': 'Database Migration',
        'assigned_to': 'sarah_dev',
        'status': 'in_progress',
        'priority': 'urgent',
        'progress': 50,
        'due_days': 5,
    },
    {
        'title': 'Create Migration Scripts',
        'description': 'Write automated migration scripts',
        'project': 'Database Migration',
        'assigned_to': 'john_dev',
        'status': 'todo',
        'priority': 'high',
        'progress': 0,
        'due_days': 14,
    },
    {
        'title': 'Test Data Integrity',
        'description': 'Verify data integrity after migration',
        'project': 'Database Migration',
        'assigned_to': 'sarah_dev',
        'status': 'todo',
        'priority': 'high',
        'progress': 0,
        'due_days': 21,
    },
]

task_count = 0
for task_data in tasks_data:
    try:
        project = created_projects.get(task_data['project'])
        assigned_user = created_users.get(task_data['assigned_to'])
        
        if project and assigned_user:
            task = Task.objects.create(
                title=task_data['title'],
                description=task_data['description'],
                project=project,
                assigned_to=assigned_user,
                assigned_by=admin_user,
                status=task_data['status'],
                priority=task_data['priority'],
                progress=task_data['progress'],
                due_date=datetime.now() + timedelta(days=task_data['due_days']),
                estimated_hours=random.randint(4, 40),
                tags='development,testing,urgent' if task_data['priority'] in ['urgent', 'high'] else 'development'
            )
            task_count += 1
            print(f"  ✅ Created task: {task_data['title']} → {assigned_user.first_name}")
    except Exception as e:
        print(f"  ❌ Error creating task: {e}")

# ============ Summary ============
print("\n" + "=" * 60)
print("📊 DEMO DATA SETUP COMPLETE!")
print("=" * 60)
print(f"\n✅ Users created: {len(created_users)}")
print(f"✅ Projects created: {len(created_projects)}")
print(f"✅ Tasks created: {task_count}")
print("\n" + "=" * 60)
print("🔑 TEST CREDENTIALS:")
print("=" * 60)
print("\nAdmin Account (Full Access):")
print("  Username: admin")
print("  Password: admin@123")

print("\nDeveloper Accounts (Can view/update assigned tasks):")
for username in ['john_dev', 'sarah_dev']:
    print(f"  Username: {username}")

print("\nManager Accounts (Can create projects & assign tasks):")
for username in ['mike_manager', 'lisa_manager']:
    print(f"  Username: {username}")

print("\n🔗 Access the application:")
print("  Dashboard: http://localhost:8000")
print("  Tasks: http://localhost:8000/tasks/")
print("  Projects: http://localhost:8000/projects/")
print("  Admin: http://localhost:8000/admin/")

print("\n" + "=" * 60)
print("Password for all test accounts: test@123")
print("=" * 60 + "\n")
