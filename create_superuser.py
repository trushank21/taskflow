import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import UserProfile

# Create superuser
username = 'admin'
email = 'admin@taskmanager.com'
password = 'admin@123'

if not User.objects.filter(username=username).exists():
    user = User.objects.create_superuser(username, email, password)
    print(f"✅ Superuser '{username}' created successfully!")
    print(f"   Email: {email}")
    print(f"   Password: {password}")
    
    # Create UserProfile
    UserProfile.objects.create(user=user, role='admin')
    print(f"✅ UserProfile created with admin role!")
else:
    print(f"⚠️  Superuser '{username}' already exists!")
