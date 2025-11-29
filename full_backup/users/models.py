from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Administrator'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
        ('parent', 'Parent'),
        ('registrar', 'Registrar'),
        ('finance', 'Finance Officer'),
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.username} ({self.role})"

class AdminProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.CharField(max_length=100)
    
    def __str__(self):
        return f"Admin: {self.user.username}"

class TeacherProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.CharField(max_length=100)
    qualification = models.TextField()
    hire_date = models.DateField()
    
    def __str__(self):
        return f"Teacher: {self.user.get_full_name()}"

class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_id = models.CharField(max_length=20, unique=True)
    program = models.CharField(max_length=100)
    semester = models.IntegerField(default=1)
    enrollment_date = models.DateField()
    
    def __str__(self):
        return f"Student: {self.user.get_full_name()} ({self.student_id})"
    class ParentProfile(models.Model):
        user = models.OneToOneField(User, on_delete=models.CASCADE)
    parent_id = models.CharField(max_length=20, unique=True)
    occupation = models.CharField(max_length=100, blank=True)
    relationship = models.CharField(max_length=50, default='Parent')  # Father, Mother, Guardian
    
    def __str__(self):
        return f"Parent: {self.user.get_full_name()}"
class RegistrarProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    office = models.CharField(max_length=100)
    
    def __str__(self):
        return f"Registrar: {self.user.username}"

class FinanceProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    finance_id = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return f"Finance: {self.user.username}"
    