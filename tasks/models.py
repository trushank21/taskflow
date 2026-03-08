from django.db import models
from django.contrib.auth.models import User
from projects.models import Project
from cloudinary.models import CloudinaryField
from django.db.models.signals import post_delete
from django.dispatch import receiver
import cloudinary.uploader

class Task(models.Model):
    """Main Task model"""
    STATUS_CHOICES = (
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('in_review', 'In Review'),
        ('completed', 'Completed'),
        ('blocked', 'Blocked'),
    )
    
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )
    days = models.DecimalField(max_digits=5, decimal_places=2, default=0.1)
    change_request_no = models.CharField(max_length=50, blank=True, null=True)
    change_request_type = models.CharField(
        max_length=10, 
        choices=[('MAJOR', 'MAJOR'), ('MINOR', 'MINOR')], 
        blank=True, 
        null=True
    )
    display_id = models.IntegerField(unique=True, editable=False, null=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks')
    assigned_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_tasks')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo',db_index=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    due_date = models.DateTimeField(blank=True, null=True)
    estimated_hours = models.FloatField(blank=True, null=True, help_text="Estimated hours to complete")
    actual_hours = models.FloatField(blank=True, null=True, help_text="Actual hours spent")
    progress = models.IntegerField(default=0, help_text="Progress percentage (0-100)")
    tags = models.CharField(max_length=255, blank=True, null=True, help_text="Comma-separated tags")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['assigned_to']),
            models.Index(fields=['project']),
        ]

    def get_status_history(self):
        return self.history.all().select_related('changed_by')

    def save(self, *args, **kwargs):
        if not self.display_id:
            # Look for the highest display_id currently assigned
            last_task = Task.objects.order_by('-display_id').first()
            if last_task and last_task.display_id:
                self.display_id = last_task.display_id + 1
            else:
                # If this is the very first task ever, start at 1
                self.display_id = 1
        super().save(*args, **kwargs)
    
    # def sync_status_and_progress(self):
    #     """
    #     Centralized Business Logic:
    #     Ensures Status and Progress are always logically synced.
    #     """
    #     # 1. Force 100% for completed tasks, or force 'completed' if progress is 100
    #     if self.status == 'completed' or self.progress == 100:
    #         self.status = 'completed'
    #         self.progress = 100
        
    #     # 2. Handle the 'In Review' state at 90%
    #     elif self.progress == 90 or self.status == 'in_review':
    #         self.status = 'in_review'
    #         self.progress = 90
            
    #     # 3. Handle 'To Do' state at 0% (unless Blocked)
    #     elif self.progress == 0:
    #         if self.status != 'blocked':
    #             self.status = 'todo'
        
    #     # 4. Handle active work transitions
    #     elif 0 < self.progress < 100:
    #         # If a task was Todo or Completed but now has mid-range progress, mark it In Progress
    #         if self.status in ['todo', 'completed']:
    #             self.status = 'in_progress'

    # def save(self, *args, **kwargs):
    #     # Run the sync logic before writing to the database
    #     self.sync_status_and_progress()
    #     super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.get_priority_display()}] {self.title}"


class TaskComment(models.Model):
    """Comments on tasks"""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    commented_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='task_comments')
    comment = models.TextField()
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.commented_by.username if self.commented_by else 'Unknown'} on {self.task.title}"


class TaskAttachment(models.Model):
    """File attachments for tasks"""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='attachments')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='task_attachments')
    # file = models.FileField(upload_to='task_attachments/')
    file = CloudinaryField('resource', folder='task_attachments/')
    file_name = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.file_name} - {self.task.title}"

class TaskHistory(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='history')
    old_status = models.CharField(max_length=50)
    new_status = models.CharField(max_length=50)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-changed_at']

@receiver(post_delete, sender=TaskAttachment)
def delete_cloudinary_file(sender, instance, **kwargs):
    if instance.file:
        try:
            # CloudinaryField stores the reference; we get the public_id from it
            public_id = getattr(instance.file, 'public_id', None)
            r_type = getattr(instance.file, 'resource_type', 'image')
            if public_id:
                cloudinary.uploader.destroy(public_id, resource_type=r_type)
        except Exception as e:
            print(f"Error deleting from Cloudinary: {e}")


