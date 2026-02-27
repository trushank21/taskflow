# TaskManager - Quick Start Guide

## ⚡ Quick Start (30 seconds)

### 1. Virtual Environment Already Created
```powershell
cd c:\Users\HP\Desktop\Django\taskmanager
.\venv\Scripts\Activate.ps1
```

### 2. Database Already Configured
- Using SQLite (development) - perfect for testing!
- Database file: `db.sqlite3`
- Admin created with credentials:
  - Username: **admin**
  - Password: **admin@123**

### 3. Start Server
```powershell
python manage.py runserver
```

### 4. Open Application
```
http://localhost:8000
```

---

## 🔑 Login Credentials

### Demo Account (Admin)
- **Username:** admin
- **Password:** admin@123

### Demo Account (Manager)
Create one by:
1. Go to Django Admin: http://localhost:8000/admin
2. Login with admin credentials
3. Create new user with Manager role

---

## 🌐 Available URLs

### Authentication
- `http://localhost:8000/login/` - Login page
- `http://localhost:8000/logout/` - Logout

### Dashboard
- `http://localhost:8000/` - Main dashboard with task overview

### Tasks
- `http://localhost:8000/tasks/` - List all tasks with filtering
- `http://localhost:8000/tasks/create/` - Create new task
- `http://localhost:8000/tasks/<id>/` - View task details
- `http://localhost:8000/tasks/<id>/edit/` - Edit task
- `http://localhost:8000/tasks/<id>/delete/` - Delete task
- `http://localhost:8000/tasks/<id>/comment/` - Add comment
- `http://localhost:8000/tasks/<id>/status/` - Update task status

### Projects
- `http://localhost:8000/projects/` - List all projects
- `http://localhost:8000/projects/create/` - Create new project
- `http://localhost:8000/projects/<id>/` - View project details
- `http://localhost:8000/projects/<id>/edit/` - Edit project
- `http://localhost:8000/projects/<id>/delete/` - Delete project

### Admin Panel
- `http://localhost:8000/admin/` - Django admin panel
  - Manage users and their roles
  - View all tasks and projects
  - Configure system settings

---

## 📊 Admin Panel Features

### Users Management
1. Go to Admin Panel: http://localhost:8000/admin
2. Click on "User Profiles"
3. Modify user roles:
   - **Admin** - Full system access
   - **Manager** - Can create projects and assign tasks
   - **Developer** - Can view and update assigned tasks

### Task Management
- View all tasks in a list
- Filter by status, priority, project
- Edit tasks inline
- Add comments through admin interface

### Project Management
- Create and manage projects
- Assign team members
- Set team leads
- Manage project status

---

## 🎯 First Steps

### Step 1: Create a Project
1. Login to http://localhost:8000
2. Click "Projects" in sidebar
3. Click "New Project"
4. Fill in:
   - Project Name
   - Description
   - Select Team Members
   - Set dates
5. Click Create

### Step 2: Create a Task
1. Click "My Tasks" in sidebar
2. Click "Create Task" 
3. Fill in:
   - Task Title
   - Select Project
   - Assign to a team member
   - Set Priority and Status
4. Click Create

### Step 3: Filter Tasks
1. Go to "My Tasks"
2. Use filters:
   - 🔍 Search by title
   - 📋 Filter by status
   - ⚡ Filter by priority
   - 👤 Filter by assignee
   - 📅 Filter by date range

### Step 4: Collaborate
1. Open task details
2. Add comments
3. Attach files
4. Update progress
5. Change status

---

## 🔧 Useful Commands

### Run Development Server
```powershell
python manage.py runserver
```

### Create Database Tables
```powershell
python manage.py migrate
```

### Create New Migration
```powershell
python manage.py makemigrations
```

### Run Django Shell (Interactive)
```powershell
python manage.py shell
```

### Create Superuser
```powershell
python manage.py createsuperuser
```

### Collect Static Files (Production)
```powershell
python manage.py collectstatic
```

---

## 🎨 UI Features

### Dashboard
- 📊 Task statistics cards
- ⚠️ Urgent tasks section
- 📅 Recent tasks display
- 🚀 Quick action buttons

### Task List
- 🔍 Advanced filtering
- 📊 Status badges with colors
- ⚡ Priority indicators
- 👤 Assignee avatars
- 📈 Progress bars

### Task Details
- 💬 Comments section
- 📎 File attachments
- 📝 Description and notes
- ⏱️ Time tracking (estimated vs actual)
- 📍 Status history

### Responsive Design
- ✅ Works on Desktop
- ✅ Works on Tablet
- ✅ Works on Mobile
- ✅ Touch-friendly buttons

---

## 🛡️ User Roles & Permissions

### Admin Role
- ✅ Create/Edit/Delete projects
- ✅ Assign tasks to anyone
- ✅ View all tasks and projects
- ✅ Manage user roles
- ✅ Access admin panel

### Manager Role
- ✅ Create/Edit projects
- ✅ Assign tasks to developers
- ✅ View all projects and tasks
- ✅ Cannot manage users
- ✅ Can use admin panel (limited)

### Developer Role
- ✅ View assigned tasks
- ✅ Update task status
- ✅ Add comments
- ✅ View projects they're added to
- ✅ Cannot create projects
- ✅ Cannot assign tasks

---

## 🐛 Troubleshooting

### Port 8000 Already in Use
```powershell
python manage.py runserver 8080
# Visit http://localhost:8080
```

### Database Issues
```powershell
# Reset database
rm db.sqlite3
python manage.py migrate
python manage.py create_superuser.py
```

### Static Files Not Loading
```powershell
python manage.py collectstatic --noinput
```

### Import Errors
```powershell
# Reinstall dependencies
pip install -r requirements.txt
```

---

## 📝 Project Structure Quick Reference

```
📁 taskmanager/
  📁 accounts/       → User profiles & authentication
  📁 projects/       → Project management
  📁 tasks/          → Task management & filtering
  📁 templates/      → HTML templates
    📁 accounts/     → Login, profile pages
    📁 tasks/        → Task pages
    📁 projects/     → Project pages
  📁 static/         → CSS, JS, Images
  📁 venv/           → Virtual environment
  
  📄 manage.py       → Django management script
  📄 db.sqlite3      → Database file
  📄 README.md       → Full documentation
```

---

## 🚀 Next Steps

1. **Test the Application**
   - Create a project
   - Assign tasks
   - Add comments
   - Try filters

2. **Create More Users**
   - Go to Admin Panel
   - Add developers and managers
   - Assign them to projects

3. **Customize Colors**
   - Edit `templates/base.html`
   - Modify CSS variables in `<style>` tag

4. **Deploy to Production**
   - Switch to MySQL database
   - Collect static files
   - Configure web server (Nginx/Apache)
   - Use WSGI server (Gunicorn)

5. **Add Features**
   - Email notifications
   - Real-time updates
   - Mobile app
   - Advanced reporting

---

## 📞 Support

For any issues:
1. Check the README.md file
2. Review Django documentation
3. Check browser console for errors
4. Verify database connection

---

**Happy Task Managing! 🎉**

Made with ❤️ for professional teams  
*TaskManager - Your Ultimate Task Management Solution*
