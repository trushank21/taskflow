# Task Creation Troubleshooting Guide

## ✅ What I've Fixed

1. **Form Validation** - Added proper field validation
2. **Error Display** - Added error messages in the form template
3. **Field Requirements** - Clearly marked required vs optional fields
4. **Default Values** - Set progress to 0% by default

---

## 🔍 Checklist Before Creating Tasks

### 1. **Projects Must Exist**
   - If you see an empty "Project" dropdown, you need to create projects first
   - Create projects at: `/projects/` → Click "Create Project"
   - Or go to Admin → Projects → Add Project

### 2. **Required Fields to Fill**
   - ✅ **Title** (required) - Task name
   - ✅ **Project** (required) - Must select one
   - ✅ **Status** (required) - Select from: To Do, In Progress, In Review, Completed, Blocked
   - ✅ **Priority** (required) - Select from: Low, Medium, High, Urgent
   
### 3. **Optional Fields**
   - ⭕ Description - Can leave blank
   - ⭕ Assign To - Leave blank if unassigned
   - ⭕ Due Date - Optional
   - ⭕ Estimated Hours - Optional
   - ⭕ Actual Hours - Optional  
   - ⭕ Progress - Defaults to 0%
   - ⭕ Tags - Optional

---

## 📝 Step-by-Step Task Creation

### **Method 1: From Dashboard**
1. Click **"+ Create Task"** button on dashboard
2. Fill in form fields:
   - Enter **Title**
   - Enter **Description** (optional)
   - Select **Project** from dropdown
   - Select **Assign To** (optional) 
   - Select **Status** (default: To Do)
   - Select **Priority** (default: Medium)
   - Adjust other fields as needed
3. Click **"Create Task"** button
4. Should see success message and be redirected to task details

### **Method 2: From Task List**
1. Go to `/tasks/`
2. Look for **"Create New Task"** button (top right)
3. Fill in form (same as Method 1)
4. Click **"Create Task"**

### **Method 3: From Admin Panel**
1. Go to `/admin/`
2. Click **"Tasks"** → **"+ Add Task"**
3. Fill in fields
4. Click **"Save"**

---

## ⚠️ Common Issues & Solutions

### **Issue: "Select a valid choice" error**
**Problem:** You selected an invalid option from dropdown
**Solution:**
- Refresh the page
- Try selecting the option again
- If dropdowns are empty, create the missing data (projects/users)

### **Issue: No projects in dropdown**
**Problem:** No projects exist in the system
**Solution:**
1. Go to `/projects/`
2. Click **"Create New Project"**
3. Fill in project details
4. Click **"Create Project"**
5. Now try creating task again

### **Issue: No users in "Assign To" dropdown**
**Problem:** No other users created yet
**Solution:**
- It's OK to leave this blank (unassigned)
- Or create users via Registration (`/accounts/register/`)
- Or use Admin to create users

### **Issue: Form keeps showing errors**
**Problem:** One or more required fields are empty
**Solution:**
- Check for red **asterisk (*)** - those fields are required
- Make sure **Project** is selected
- Make sure **Status** is selected
- Make sure **Priority** is selected

### **Issue: Task is created but I don't see it in the list**
**Problem:** Might be filtering issue
**Solution:**
- Go to `/tasks/`
- Check if filters are applied (bottom left)
- Try clearing filters
- Check your assigned tasks

---

## 🧪 Test Task Creation (Verified Working)

Here's a guaranteed working example:

**Minimum Fields:**
- Title: "Test Task"
- Project: "Website Redesign" (or any existing project)
- Status: "To Do"
- Priority: "Medium"

**Click Create → Task is Created ✅**

---

## 📊 Task Creation Flow

```
1. User clicks "Create Task"
   ↓
2. Form page loads with empty fields
   ↓
3. Fill in REQUIRED fields:
   - Title
   - Project
   - Status  
   - Priority
   ↓
4. (Optional) Fill optional fields
   ↓
5. Click "Create Task" button
   ↓
6. Form validates all fields
   ↓
7. If valid → Task created and saved to database
   ↓
8. User redirected to task details page
   ↓
9. Success message shown
```

---

## 🛠️ Technical Details

**Form Type:** Django ModelForm for Task model  
**Required Validations:**
- Title: Max 255 characters
- Project: Must exist in Projects table
- Status: Must be valid choice (todo/in_progress/in_review/completed/blocked)
- Priority: Must be valid choice (low/medium/high/urgent)
- Progress: 0-100 (defaults to 0)

**Database Table:** `tasks_task`

---

## 🔧 Commands to Test

```bash
# Check if projects exist
python manage.py shell
>>> from projects.models import Project
>>> Project.objects.all().count()

# Check if tasks exist
>>> from tasks.models import Task
>>> Task.objects.all().count()

# Create test task manually
>>> from django.contrib.auth.models import User
>>> admin = User.objects.get(username='admin')
>>> project = Project.objects.first()
>>> Task.objects.create(
...     title='Test',
...     project=project,
...     assigned_by=admin,
...     status='todo',
...     priority='medium'
... )
```

---

## 📞 If Still Having Issues

1. **Check browser console** for JavaScript errors (F12)
2. **Check server logs** for Python errors
3. **Verify project exists** - Go to `/projects/`
4. **Try test task creation** using shell commands above
5. **Clear browser cache** - Ctrl+Shift+Delete

---

## ✨ What Should Happen

### When You Submit Valid Form:
```
✅ Form validates
✅ Task created in database
✅ assigned_by field auto-fills with current user
✅ progress defaults to 0%
✅ Redirects to task detail page  
✅ Success message shows: "Task created successfully!"
✅ Task appears in task list
✅ Can edit progress/status from task detail page
```

---

**Last Updated:** February 18, 2026
