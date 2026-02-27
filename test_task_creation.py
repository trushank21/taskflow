#!/usr/bin/env python
"""Test task creation - Debug script"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth.models import User
from projects.models import Project
from tasks.models import Task
from tasks.forms import TaskForm

print("=" * 60)
print("Task Creation Test")
print("=" * 60)

# Get admin user
try:
    admin = User.objects.get(username='admin')
    print(f"✅ Admin user found: {admin.username}")
except User.DoesNotExist:
    print("❌ Admin user not found!")
    sys.exit(1)

# Get or check projects
projects = Project.objects.all()
if not projects.exists():
    print("❌ No projects found! Create a project first.")
    sys.exit(1)

project = projects.first()
print(f"✅ Using project: {project.title}")

# Test form data
form_data = {
    'title': 'Test Task',
    'description': 'This is a test task',
    'project': project.id,
    'assigned_to': admin.id,
    'status': 'todo',
    'priority': 'medium',
    'progress': 0,
    'due_date': '',
    'estimated_hours': '',
    'actual_hours': '',
    'tags': '',
}

print("\n📝 Creating task with form data:")
for key, value in form_data.items():
    print(f"  {key}: {value}")

# Test form validation
print("\n🔍 Validating form...")
form = TaskForm(form_data)

if form.is_valid():
    print("✅ Form is VALID")
    print("\n💾 Saving task...")
    task = form.save(commit=False)
    task.assigned_by = admin
    task.save()
    print(f"✅ Task created successfully!")
    print(f"   Task ID: {task.id}")
    print(f"   Title: {task.title}")
    print(f"   Status: {task.status}")
    print(f"   Progress: {task.progress}%")
else:
    print("❌ Form is INVALID")
    print("\nForm errors:")
    for field, errors in form.errors.items():
        for error in errors:
            print(f"  {field}: {error}")
    
    if form.non_field_errors():
        print("\nNon-field errors:")
        for error in form.non_field_errors():
            print(f"  {error}")

print("\n" + "=" * 60)
