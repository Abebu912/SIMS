import os
import sys
from pathlib import Path

# Ensure project root is on sys.path so imports work when running this script
BASE_DIR = Path(__file__).resolve().parents[0]
sys.path.insert(0, str(BASE_DIR))

import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sims.settings")
django.setup()

from users.models import CustomUser
from students.models import Student
from courses.models import Course

# Create admin user
if not CustomUser.objects.filter(username="admin").exists():
    admin = CustomUser.objects.create_superuser(
        username="admin",
        email="admin@sims.local",
        password="admin123",
        role="admin"
    )
    print("Admin user created")

# Create sample users
roles = [
    ("teacher1", "Teacher", "teacher"),
    ("student1", "Student One", "student"),
    ("parent1", "Parent One", "parent"),
]

for username, name, role in roles:
    if not CustomUser.objects.filter(username=username).exists():
        user = CustomUser.objects.create_user(
            username=username,
            email=f"{username}@sims.local",
            password="test123",
            first_name=name.split()[0],
            role=role
        )
        if role == "student":
            Student.objects.create(
                user=user,
                student_id=f"STU{username[-1]}001",
                grade_level=1
            )
        print(f"User {username} created")

# Create sample courses
courses_data = [
    ("MATH101", "Mathematics", "Introduction to calculus"),
    ("ENG101", "English", "English literature and composition"),
    ("SCI101", "Science", "General science concepts"),
]

for code, name, desc in courses_data:
    if not Course.objects.filter(code=code).exists():
        Course.objects.create(
            code=code,
            name=name,
            description=desc,
            teacher=CustomUser.objects.filter(role="teacher").first()
        )
        print(f"Course {code} created")

print("Initial data setup complete!")
