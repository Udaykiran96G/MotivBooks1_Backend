import google.generativeai as genai
import os
import django
import sys

# Setup Django environment
sys.path.append(r"c:\Users\udayu\AndroidStudioProjects\EBOOKMOTIVATION\backend")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_config.settings')
django.setup()

from django.conf import settings

try:
    genai.configure(api_key=settings.GEMINI_API_KEY)
    print("Available Models:")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
except Exception as e:
    print(f"Error: {e}")
