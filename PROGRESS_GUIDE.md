# Task Progress Guide

## How Progress Increases

There are **3 ways to update task progress** in the TaskManager system:

---

## 1. Quick Progress Update (Task Details Page)

The **fastest way** to update progress is from the task details page:

### Steps:
1. Open any task by clicking on it in the task list
2. Scroll down to the **"Update Progress"** section
3. Drag the **progress slider** left or right (adjusts in 5% increments)
4. Watch the percentage badge update in real-time
5. Click **"Save"** button to save the change
6. You'll see a success message confirming the update

### Visual Feedback:
- The slider shows your current progress percentage
- The badge displays the selected value
- The progress bar at the top updates after you save

**Best for:** Quick daily updates while working on tasks

---

## 2. Edit Task Form

Update progress when editing task details:

### Steps:
1. Open a task from the task list
2. Click **"Edit Task"** button
3. Scroll to the **"Progress"** field
4. Use the slider to adjust progress (0-100%)
5. Update other fields if needed
6. Click **"Save"** to apply all changes

### Which fields you can update:
- ✅ Task Title
- ✅ Description
- ✅ Project Assignment
- ✅ Assigned To (reassign task)
- ✅ Status
- ✅ Priority
- ✅ **Progress** ← Drag slider
- ✅ Due Date
- ✅ Estimated Hours
- ✅ Actual Hours Spent
- ✅ Tags

**Best for:** Making multiple changes at once

---

## 3. Admin Panel

Update progress through Django admin interface:

### Steps:
1. Go to `/admin/` (Admin Panel)
2. Navigate to **"Tasks"** section
3. Click on the task you want to edit
4. Find the **"Progress"** field
5. Enter percentage (0-100)
6. Scroll down and click **"Save"**

**Best for:** Bulk updates and administrative changes

---

## Progress Percentage Guide

| Progress | Status | Meaning |
|----------|--------|---------|
| 0% | Not Started | Task created but not started yet |
| 1-25% | Just Started | Initial work has begun |
| 26-50% | Halfway | Task is progressing well |
| 51-75% | Almost Done | Final stages of work |
| 76-99% | Nearly Complete | Waiting for final review/testing |
| 100% | Complete | Task finished (consider changing status to "Completed") |

---

## Progress Tips & Best Practices

### 1. **Update Progress Regularly**
   - Update progress as you work on tasks
   - Review at the end of each day
   - Helps track team productivity

### 2. **Align Progress with Status**
   - When progress reaches 100%, update status to "Completed"
   - Use status "In Progress" when progress is 1-99%
   - Use status "In Review" when progress is 90%+ and waiting approval

### 3. **Use Actual Hours to Calculate Progress**
   - Add estimated hours when creating task
   - Track actual hours spent
   - Drag progress to match actual progress made
   - Example: If 5 hours estimated and 2.5 hours spent, set progress to ~50%

### 4. **Progress vs Status**
   - **Progress (%)**: How much work is completed (visual percentage)
   - **Status**: Current workflow stage (todo/in_progress/completed)
   
   Example: A task can be:
   - Status: "In Review" | Progress: 95% (waiting code review)
   - Status: "Completed" | Progress: 100% (all done)

---

## Viewing Progress Across System

### Dashboard
- See urgent tasks with their current progress
- Quick glance at team workload

### Task List
- Progress bars visible in the table
- Filter/sort by progress levels
- Identify stalled tasks (0% or low progress)

### Task Details
- Large progress bar showing current completion
- Detailed progress update form
- Task timeline and history

### Project View
- See aggregate progress across all project tasks
- Visual breakdown by task status and progress

---

## Auto-Progress Features

Currently, progress is **manual** (you control it). 

Future enhancements might include:
- Auto-progress based on status changes
- Progress auto-calculated from hour tracking
- Burndown charts showing progress over time
- Progress predictions based on velocity

---

## Troubleshooting

### Q: Why doesn't progress update after I drag the slider?
A: You must click the **"Save"** button to store the change. Dragging only shows the preview.

### Q: Can I set progress to more than 100%?
A: No, the system limits progress to 0-100%. This is intentional to maintain data integrity.

### Q: Does changing progress affect the task status?
A: No, progress and status are independent. Update status separately if needed.

### Q: Who can update progress?
A: Any user (developer/manager) assigned to or can view the task can update progress. Admins can always update any task.

---

## Example Workflow

**Day 1: Create Task**
- Create: "Implement User Login Feature"
- Progress: 0%
- Status: "To Do"

**Day 1 Afternoon: Start Work**
- Progress: 15%
- Status: "In Progress"
- Add actual hours: 2h

**Day 2: Continue Work**
- Progress: 50%
- Status: "In Progress"
- Add actual hours: 4h total

**Day 3: Code Review**
- Progress: 95%
- Status: "In Review"
- Add actual hours: 5h total

**Day 4: Approved & Merged**
- Progress: 100%
- Status: "Completed"
- Add actual hours: 6h total

---

## Quick Links
- [Task List](http://localhost:8000/tasks/) - View all tasks
- [Dashboard](http://localhost:8000/) - See urgent tasks
- [Create New Task](http://localhost:8000/tasks/create/) - Start new task
- [Admin Panel](http://localhost:8000/admin/) - Admin controls

---

**Last Updated:** February 17, 2026  
**Version:** 1.0
