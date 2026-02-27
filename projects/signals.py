from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver
from .models import Project
from django.contrib.auth.models import User

@receiver(post_save, sender=Project)
def add_core_members_on_create(sender, instance, created, **kwargs):
    """Initial add when the project is first created."""
    if created:
        # 1. Add the Team Lead (Manager)
        if instance.team_lead:
            instance.team_members.add(instance.team_lead)

        # 2. Add the Creator (Admin) - Moved outside the team_lead block
        if hasattr(instance, 'created_by') and instance.created_by:
            instance.team_members.add(instance.created_by)

# @receiver(m2m_changed, sender=Project.team_members.through)
# def enforce_core_membership(sender, instance, action, **kwargs):
#     """
#     Ensures the superuser 'admin', the creator, and the team lead 
#     are ALWAYS in the team_members list.
#     """
#     # We trigger on post_add, post_remove, and post_clear to catch all changes
#     if action in ["post_add", "post_remove", "post_clear"]:
#         to_add = []

#         # 1. Target the Superuser named 'admin' specifically
#         try:
#             superuser_admin = User.objects.get(username='admin')
#             if not instance.team_members.filter(pk=superuser_admin.pk).exists():
#                 to_add.append(superuser_admin.pk)
#         except User.DoesNotExist:
#             pass 

#         # 2. Ensure the Creator (instance.created_by) is present
#         if instance.created_by and not instance.team_members.filter(pk=instance.created_by.pk).exists():
#             to_add.append(instance.created_by.pk)

#         # 3. Ensure Team Lead is present
#         if instance.team_lead and not instance.team_members.filter(pk=instance.team_lead.pk).exists():
#             to_add.append(instance.team_lead.pk)

#         # Add them all back if any are missing
#         if to_add:
#             instance.team_members.add(*to_add)


@receiver(m2m_changed, sender=Project.team_members.through)
def enforce_core_membership(sender, instance, action, pk_set, **kwargs):
    # Only run on actions that could potentially leave the list without core members
    if action in ["post_add", "post_remove", "post_clear"]:
        
        # 1. Identify Protected Pks
        protected_pks = set()
        if instance.team_lead:
            protected_pks.add(instance.team_lead.pk)
        if instance.created_by:
            protected_pks.add(instance.created_by.pk)
        
        superusers = User.objects.filter(is_superuser=True).values_list('pk', flat=True)
        protected_pks.update(superusers)

        # 2. Check current state
        current_members = set(instance.team_members.values_list('pk', flat=True))
        missing_pks = protected_pks - current_members

        # 3. THE FIX: Only call .add() if there's actually something missing
        if missing_pks:
            # Disconnect to prevent the post_add loop
            m2m_changed.disconnect(enforce_core_membership, sender=Project.team_members.through)
            
            instance.team_members.add(*missing_pks)
            
            # Reconnect
            m2m_changed.connect(enforce_core_membership, sender=Project.team_members.through)