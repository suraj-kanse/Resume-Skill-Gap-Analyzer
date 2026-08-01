import os
import django
from django.core.management import call_command

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_skill_gap.settings')
django.setup()

print("1. Running makemigrations...")
call_command('makemigrations')

print("2. Running migrate...")
call_command('migrate')

print("Database migrated successfully!")
