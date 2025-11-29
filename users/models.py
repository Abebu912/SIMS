from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

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
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.username} ({self.role})"

class AdminProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.CharField(max_length=100, default='Administration')
    
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
    GRADE_CHOICES = [
        (1, 'Grade 1'),
        (2, 'Grade 2'),
        (3, 'Grade 3'),
        (4, 'Grade 4'),
        (5, 'Grade 5'),
        (6, 'Grade 6'),
        (7, 'Grade 7'),
        (8, 'Grade 8'),
    ]
    
    SEMESTER_CHOICES = [
        ('first', 'First Semester'),
        ('second', 'Second Semester'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_id = models.CharField(max_length=20, unique=True)
    grade_level = models.IntegerField(choices=GRADE_CHOICES, default=1)
    current_semester = models.CharField(max_length=10, choices=SEMESTER_CHOICES, default='first')
    academic_year = models.CharField(max_length=9, default='2024-2025')
    enrollment_date = models.DateField(auto_now_add=True)
    
    def __str__(self):
        return f"Student: {self.user.get_full_name()} (Grade {self.grade_level})"
    
    def save(self, *args, **kwargs):
        if not self.student_id:
            self.student_id = f"STU{self.user.id:06d}"
        super().save(*args, **kwargs)
    
    def get_available_semesters(self):
        return ['first', 'second']
    
    def get_academic_year_display(self):
        return f"{self.academic_year} - {self.get_current_semester_display()}"
    
    def get_current_semester_display(self):
        return dict(self.SEMESTER_CHOICES).get(self.current_semester, 'Unknown')

class RegistrarProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    office = models.CharField(max_length=100, default='Registrar Office')
    
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
    relationship = models.CharField(max_length=50, default='Parent')
    
    def __str__(self):
        return f"Parent: {self.user.get_full_name()}"

class StudentParent(models.Model):
    parent = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'parent'}, related_name='parent_relationships')
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'student'}, related_name='student_relationships')
    relationship = models.CharField(max_length=50, default='Parent')
    is_primary = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['parent', 'student']
    
    def __str__(self):
        return f"{self.parent.username} -> {self.student.username}"