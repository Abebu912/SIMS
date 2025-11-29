from django.db import models
from django.utils import timezone
from users.models import User
from subjects.models import Subject
from datetime import datetime

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="student_profile")
    student_id = models.CharField(max_length=50, unique=True)
    grade_level = models.IntegerField(default=1)
    parent = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="children")
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)
    enrollment_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.student_id} - {self.user.first_name} {self.user.last_name}"
    
    @property
    def academic_year(self):
        """Get current academic year in format YYYY-YYYY"""
        now = datetime.now()
        current_year = now.year
        current_month = now.month
        
        # Academic year typically starts in August/September
        # If current month is before August, use previous year as start
        if current_month < 8:
            start_year = current_year - 1
        else:
            start_year = current_year
        
        end_year = start_year + 1
        return f"{start_year}-{end_year}"
    
    @property
    def current_semester(self):
        """Get current semester ('first' or 'second')"""
        current_month = datetime.now().month
        # First semester: August - December (8-12)
        # Second semester: January - May (1-5)
        if current_month in [8, 9, 10, 11, 12]:
            return 'first'
        else:
            return 'second'
    
    def get_current_semester_display(self):
        """Get human-readable semester name"""
        semester_display = {
            'first': 'First Semester',
            'second': 'Second Semester'
        }
        return semester_display.get(self.current_semester, 'Unknown Semester')

class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="attendance")
    date = models.DateField()
    present = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("student", "date")
