from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError
import datetime

User = get_user_model()

# ADD: Teacher Model
class Teacher(models.Model):
    DAYS_OF_WEEK = [
        ('mon', 'Monday'),
        ('tue', 'Tuesday'),
        ('wed', 'Wednesday'),
        ('thu', 'Thursday'),
        ('fri', 'Friday'),
        ('sat', 'Saturday'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    teacher_id = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15, blank=True)
    office_location = models.CharField(max_length=50, blank=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.teacher_id})"

# UPDATE: Subject Model - ADD THESE FIELDS
class Subject(models.Model):
    GRADE_LEVEL_CHOICES = [
        (1, 'Grade 1'),
        (2, 'Grade 2'),
        (3, 'Grade 3'),
        (4, 'Grade 4'),
        (5, 'Grade 5'),
        (6, 'Grade 6'),
        (7, 'Grade 7'),
        (8, 'Grade 8'),
    ]
    
    SUBJECT_TYPES = [
        ('core', 'Core'),
        ('elective', 'Elective'),
        ('lab', 'Laboratory'),
    ]
    
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    
    # CHANGE: credits to credit_hours
    credit_hours = models.PositiveIntegerField(default=3, help_text="Credit hours for this subject")
    
    subject_type = models.CharField(max_length=20, choices=SUBJECT_TYPES, default='core')
    grade_level = models.IntegerField(
        choices=GRADE_LEVEL_CHOICES,
        help_text="Select the grade level for this subject"
    )
    
    # UPDATE: Replace simple schedule with detailed scheduling
    day_of_week = models.CharField(max_length=3, choices=Teacher.DAYS_OF_WEEK, blank=True)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    room = models.CharField(max_length=50, blank=True)
    # Number of class sessions per week (e.g., 3 sessions/week)
    sessions_per_week = models.PositiveSmallIntegerField(default=3, help_text='Number of sessions per week')
    
    # ADD: Teacher assignment
    instructor = models.ForeignKey(
        Teacher, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='subjects'
    )
    # Mark whether this subject was assigned to the instructor by the registrar
    assigned_by_registrar = models.BooleanField(default=False)
    
    max_capacity = models.IntegerField(default=30)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.code} - {self.name} (Grade {self.grade_level})"
    
    @property
    def schedule_display(self):
        """Get formatted schedule display"""
        if self.day_of_week and self.start_time and self.end_time:
            day_name = dict(Teacher.DAYS_OF_WEEK).get(self.day_of_week, self.day_of_week)
            return f"{day_name} {self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}"
        return "Not scheduled"
    
    @property
    def duration_minutes(self):
        """Calculate class duration in minutes"""
        if self.start_time and self.end_time:
            start_dt = datetime.datetime.combine(datetime.date.today(), self.start_time)
            end_dt = datetime.datetime.combine(datetime.date.today(), self.end_time)
            return int((end_dt - start_dt).total_seconds() / 60)
        return 0
    
    def clean(self):
        """Validate subject data"""
        # Existing validation
        if Subject.objects.filter(
            code=self.code, 
            grade_level=self.grade_level
        ).exclude(id=self.id).exists():
            raise ValidationError(
                f"A subject with code '{self.code}' already exists for Grade {self.grade_level}."
            )
        
        # NEW: Validate time conflicts for teacher
        if self.day_of_week and self.start_time and self.end_time and self.instructor:
            conflicting_subjects = Subject.objects.filter(
                instructor=self.instructor,
                day_of_week=self.day_of_week,
                is_active=True
            ).exclude(pk=self.pk)
            
            for subject in conflicting_subjects:
                if (self.start_time < subject.end_time and self.end_time > subject.start_time):
                    raise ValidationError(
                        f"Time conflict with {subject.code} - {subject.schedule_display}"
                    )
        
        # NEW: Validate end time is after start time
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValidationError("End time must be after start time")
    
    def current_enrollment_count(self, academic_year, semester):
        """Get current enrollment count for this subject"""
        return self.enrollments.filter(
            academic_year=academic_year,
            semester=semester,
            status='active'
        ).count()

    def is_available(self, academic_year, semester):
        """Check if subject has available slots"""
        return self.current_enrollment_count(academic_year, semester) < self.max_capacity
    
    def available_slots(self, academic_year, semester):
        """Get number of available slots"""
        return self.max_capacity - self.current_enrollment_count(academic_year, semester)
    
    class Meta:
        ordering = ['grade_level', 'code']

# ADD: ScheduleConflict Model
class ScheduleConflict(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    conflicting_subjects = models.ManyToManyField(Subject)
    academic_year = models.CharField(max_length=20)
    semester = models.CharField(max_length=20)
    detected_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Schedule conflict for {self.student.username}"
class Enrollment(models.Model):
    SEMESTER_CHOICES = [
        ('first', 'First Semester'),
        ('second', 'Second Semester'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('waitlisted', 'Waitlisted'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('dropped', 'Dropped'),
        ('rejected', 'Rejected'),
    ]
    
    student = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='subject_enrollments',
        limit_choices_to={'role': 'student'}
    )
    subject = models.ForeignKey(
        Subject, 
        on_delete=models.CASCADE, 
        related_name='enrollments'
    )
    enrolled_date = models.DateField(default=timezone.now)
    academic_year = models.CharField(
        max_length=9,
        help_text="Format: YYYY-YYYY (e.g., 2024-2025)"
    )
    semester = models.CharField(
        max_length=10, 
        choices=SEMESTER_CHOICES, 
        default='first'
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='active'
    )
    final_grade = models.CharField(max_length=5, blank=True)
    # NEW: result field to store teacher-assigned result/remark per enrollment
    result = models.CharField(max_length=50, blank=True, null=True, help_text='Result or remark for this enrollment')
    # Mark enrollments that were automatically assigned by the system
    is_auto_assigned = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['student', 'subject', 'academic_year', 'semester']
        ordering = ['-enrolled_date']
    
    def __str__(self):
        return f"{self.student.username} - {self.subject.code} ({self.academic_year} - {self.get_semester_display()})"
    
    def clean(self):
        """Validate academic year format and semester"""
        # Validate academic year format
        if self.academic_year:
            if len(self.academic_year) != 9 or self.academic_year[4] != '-':
                raise ValidationError("Academic year should be in format YYYY-YYYY (e.g., 2024-2025)")
            try:
                start_year = int(self.academic_year[:4])
                end_year = int(self.academic_year[5:])
                if end_year != start_year + 1:
                    raise ValidationError("Academic year should be in format YYYY-YYYY (e.g., 2024-2025)")
            except ValueError:
                raise ValidationError("Academic year should be in format YYYY-YYYY (e.g., 2024-2025)")
        
        # Validate that student is enrolled in subjects matching their grade level
        if self.student.role == 'student' and hasattr(self.student, 'studentprofile'):
            student_grade = self.student.studentprofile.grade_level
            if self.subject.grade_level != student_grade:
                raise ValidationError(
                    f"Student is in Grade {student_grade} but subject is for Grade {self.subject.grade_level}"
                )
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def get_semester_display(self):
        """Get human-readable semester name"""
        return dict(self.SEMESTER_CHOICES).get(self.semester, self.semester)

class Assignment(models.Model):
    subject = models.ForeignKey(
        Subject, 
        on_delete=models.CASCADE, 
        related_name='assignments'
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    due_date = models.DateTimeField()
    max_points = models.IntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.subject.code} - {self.title}"
    
    class Meta:
        ordering = ['due_date']

class Grade(models.Model):
    enrollment = models.ForeignKey(
        Enrollment, 
        on_delete=models.CASCADE, 
        related_name='grades'
    )
    assignment = models.ForeignKey(
        Assignment, 
        on_delete=models.CASCADE, 
        related_name='grades'
    )
    points_earned = models.DecimalField(max_digits=5, decimal_places=2)
    feedback = models.TextField(blank=True)
    graded_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['enrollment', 'assignment']
    
    def __str__(self):
        return f"{self.enrollment.student.username} - {self.assignment.title}"
    
    def percentage(self):
        """Calculate percentage score"""
        if self.assignment.max_points > 0:
            return (self.points_earned / self.assignment.max_points) * 100
        return 0
    
    def letter_grade(self):
        """Convert percentage to letter grade"""
        percentage = self.percentage()
        if percentage >= 90:
            return 'A'
        elif percentage >= 80:
            return 'B'
        elif percentage >= 70:
            return 'C'
        elif percentage >= 60:
            return 'D'
        else:
            return 'F'

class Attendance(models.Model):
    enrollment = models.ForeignKey(
        Enrollment, 
        on_delete=models.CASCADE, 
        related_name='attendance_records'
    )
    date = models.DateField()
    status = models.CharField(
        max_length=10,
        choices=[
            ('present', 'Present'),
            ('absent', 'Absent'),
            ('late', 'Late'),
            ('excused', 'Excused'),
        ],
        default='present'
    )
    notes = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['enrollment', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.enrollment.student.username} - {self.date} - {self.status}"
    