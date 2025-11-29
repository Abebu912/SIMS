# fix_parent_profile.py
import os

def fix_parent_profile():
    print("🔧 Adding ParentProfile to users/models.py...")
    
    complete_models_content = '''from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Administrator'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
        ('registrar', 'Registrar'),
        ('finance', 'Finance Officer'),
        ('parent', 'Parent'),
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to=\'profiles/\', null=True, blank=True)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.username} ({self.role})"

class AdminProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.CharField(max_length=100, default=\'Administration\')
    
    def __str__(self):
        return f"Admin: {self.user.username}"

class TeacherProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.CharField(max_length=100)
    qualification = models.TextField()
    hire_date = models.DateField(auto_now_add=True)
    
    def __str__(self):
        return f"Teacher: {self.user.get_full_name()}"

class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_id = models.CharField(max_length=20, unique=True)
    program = models.CharField(max_length=100)
    semester = models.IntegerField(default=1)
    enrollment_date = models.DateField(auto_now_add=True)
    
    def __str__(self):
        return f"Student: {self.user.get_full_name()} ({self.student_id})"

class RegistrarProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    office = models.CharField(max_length=100, default=\'Registrar Office\')
    
    def __str__(self):
        return f"Registrar: {self.user.username}"

class FinanceProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    finance_id = models.CharField(max_length=20, unique=True)
    
    def __str__(self):
        return f"Finance: {self.user.username}"

class ParentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    parent_id = models.CharField(max_length=20, unique=True)
    occupation = models.CharField(max_length=100, blank=True)
    relationship = models.CharField(max_length=50, default=\'Parent\')
    
    def __str__(self):
        return f"Parent: {self.user.get_full_name()}"

class StudentParent(models.Model):
    parent = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={\'role\': \'parent\'})
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={\'role\': \'student\'})
    relationship = models.CharField(max_length=50, default=\'Parent\')
    is_primary = models.BooleanField(default=False)
    
    class Meta:
        unique_together = [\'parent\', \'student\']
    
    def __str__(self):
        return f"{self.parent.username} -> {self.student.username}"
'''

    # Write the complete models file
    with open('users/models.py', 'w', encoding='utf-8') as f:
        f.write(complete_models_content)
    
    print("✅ users/models.py updated successfully!")
    print("🚀 Now run these commands:")
    print("   1. python manage.py makemigrations users")
    print("   2. python manage.py migrate")
    print("   3. python manage.py runserver")

if __name__ == '__main__':
    fix_parent_profile()