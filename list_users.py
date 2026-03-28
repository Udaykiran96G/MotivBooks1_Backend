import os
import django
import sys

# Setup Django environment
sys.path.append(r"c:\Users\udayu\AndroidStudioProjects\EBOOKMOTIVATION\backend")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_config.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

users = User.objects.all()
print(f"Total Users: {users.count()}")
for u in users:
    print(f" - {u.email} (Active: {u.is_active})")
