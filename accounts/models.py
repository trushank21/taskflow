from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    """Extended user profile for role management"""
    ROLE_CHOICES = (
        ('admin', 'Administrator'),
        ('manager', 'Manager'),
        ('developer', 'Developer'),
        ('observer', 'Observer (View Only)'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='developer')
    department = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.get_role_display()})"

# --- SIGNALS ---
# We combine creation and saving into one receiver to ensure 
# they happen in the correct order every time.



@receiver(post_save, sender=User)
def handle_user_profile(sender, instance, created, **kwargs):
    """
    Signal to create/update UserProfile whenever a User is saved.
    """
    if created:
        # 'get_or_create' is a safety net against UNIQUE constraint errors
        UserProfile.objects.get_or_create(user=instance)
    # else:
    #     # Use hasattr to prevent crashes if a profile was never created
    #     if hasattr(instance, 'profile'):
    #         instance.profile.save()