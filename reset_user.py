import os
import django
import sys

# Setup Django environment
sys.path.append(r"c:\Users\udayu\AndroidStudioProjects\EBOOKMOTIVATION\backend")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_config.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

try:
    user = User.objects.get(email="tester5@test.com")
    user.set_password("password123")
    user.save()
    print("Password updated for tester5@test.com")
except User.DoesNotExist:
    print("User not found")
