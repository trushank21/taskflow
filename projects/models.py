from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.db.models import Avg

class Project(models.Model):
    """Project model for organizing tasks"""
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold'),
    )
    
    title = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_projects')
    team_lead = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='led_projects')
    team_members = models.ManyToManyField(User, related_name='projects_assigned', blank=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    overall_progress = models.IntegerField(default=0)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return self.title

# --- Signals ---

@receiver(post_save, sender=User)
def handle_user_profile(sender, instance, created, **kwargs):
    """Handles UserProfile creation via signal."""
    if created:
        from accounts.models import UserProfile # Local import to avoid circularity
        UserProfile.objects.get_or_create(user=instance)
    elif hasattr(instance, 'profile'):
        instance.profile.save()

# @receiver(post_save, sender='tasks.Task')
# def sync_project_status(sender, instance, **kwargs):
#     """
#     Rule B: The Ghost Activation Fix.
#     Prevents task updates from "waking up" projects that are On Hold or Inactive.
#     """
#     project = instance.project
#     if not project:
#         return

#     # RULE B: If project is on_hold or inactive, DO NOT change its status automatically
#     if project.status in ['on_hold', 'inactive']:
#         return 
    
#     has_uncompleted_tasks = project.tasks.exclude(status='completed').exists()
#     if not has_uncompleted_tasks:
#         new_status = 'completed'
#     else:
#         new_status = 'active'

#     stats = project.tasks.aggregate(avg=Avg('progress'))
#     avg_progress = stats['avg'] or 0

#     project.overall_progress = avg_progress
        
#     if project.status != new_status:
#         project.status = new_status
#         project.save(update_fields=['status','overall_progress'])

#     # Calculate average progress
#     # stats = project.tasks.aggregate(avg=Avg('progress'))
#     # progress = stats['avg'] or 0
    
#     # # Determine the correct status based on Image 1 & 2
#     # # If progress hits 100%, move to 'completed' (Image 1 logic)
#     # if progress >= 100:
#     #     new_status = 'completed'
#     # else:
#     #     new_status = 'active'
        
#     # Only save if the status actually changed
#     # if project.status != new_status:
#     #     project.status = new_status
#     #     project.save(update_fields=['status'])


@receiver(post_save, sender='tasks.Task')
def sync_project_status(sender, instance, **kwargs):
    project = instance.project
    if not project:
        return

    # 1. ALWAYS calculate the latest progress values
    stats = project.tasks.aggregate(avg=Avg('progress'))
    new_progress = stats['avg'] or 0

    # 2. Status Logic (Rule B: Don't wake up 'on_hold' or 'inactive' projects)
    new_status = project.status  # Start with the current status
    if project.status not in ['on_hold', 'inactive']:
        has_uncompleted_tasks = project.tasks.exclude(status='completed').exists()
        new_status = 'completed' if not has_uncompleted_tasks else 'active'
    
    # 3. THE DIRTY CHECK (The Performance Hero)
    # We only call .save() if the status OR the progress has actually changed.
    # If someone just changed a task name, this 'if' will be False, and we save a DB hit.
    if project.overall_progress != new_progress or project.status != new_status:
        project.overall_progress = new_progress
        project.status = new_status
        project.save(update_fields=['status', 'overall_progress'])