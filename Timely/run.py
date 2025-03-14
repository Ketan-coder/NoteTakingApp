import os
import sys
import django
from django.core.management import execute_from_command_line

# Set the Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Timely.settings")

django.setup()

# Start Django server
if __name__ == "__main__":
    execute_from_command_line(["manage.py", "runserver", "127.0.0.1:8000"])
