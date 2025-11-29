from django.db import models
from users.models import User
from subjects.models import Subject

class Grade(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'student'})
    course = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_grades', limit_choices_to={'role': 'teacher'})
    grade = models.CharField(max_length=5, null=True, blank=True)
    remarks = models.TextField(blank=True)
    graded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['student', 'course']
    
    def __str__(self):
        return f"{self.student.username} - {self.course.code}: {self.grade}"
    
    def get_grade_point(self):
        """Convert letter grade to grade point"""
        if not self.grade:
            return 0.0
            
        grade_points = {
            'A': 4.0, 'A-': 3.7,
            'B+': 3.3, 'B': 3.0, 'B-': 2.7,
            'C+': 2.3, 'C': 2.0, 'C-': 1.7,
            'D+': 1.3, 'D': 1.0, 'D-': 0.7,
            'F': 0.0
        }
        return grade_points.get(self.grade.upper(), 0.0)

class Transcript(models.Model):
    """Model to store student transcripts"""
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'student'})
    generated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='generated_transcripts', limit_choices_to={'role__in': ['admin', 'registrar']})
    generated_at = models.DateTimeField(auto_now_add=True)
    gpa = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_credits = models.IntegerField(default=0)
    academic_year = models.CharField(max_length=20, default='2023-2024')
    semester = models.CharField(max_length=20, default='All')
    is_official = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['student', 'academic_year', 'semester']
    
    def __str__(self):
        return f"Transcript: {self.student.username} - {self.academic_year} {self.semester}"
    
    def calculate_gpa(self):
        """Calculate GPA for this transcript"""
        grades = Grade.objects.filter(student=self.student)
        if self.semester != 'All':
            # Filter by semester if specified
            grades = grades.filter(course__semester=self.semester)
        
        total_points = 0
        total_credits = 0
        
        for grade in grades:
            if grade.grade and grade.course.credits:
                grade_point = grade.get_grade_point()
                total_points += grade_point * grade.course.credits
                total_credits += grade.course.credits
        
        if total_credits > 0:
            self.gpa = total_points / total_credits
            self.total_credits = total_credits
        else:
            self.gpa = 0.00
            self.total_credits = 0
        
        self.save()
        return self.gpa

class GradeScale(models.Model):
    """Model to define grade scales"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    scale_type = models.CharField(max_length=20, choices=[
        ('letter', 'Letter Grades'),
        ('percentage', 'Percentage'),
        ('points', 'Point System')
    ])
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} ({self.scale_type})"

class GradeItem(models.Model):
    """Individual grade items within a grade scale"""
    grade_scale = models.ForeignKey(GradeScale, on_delete=models.CASCADE, related_name='grade_items')
    letter_grade = models.CharField(max_length=5)
    min_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    max_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    grade_points = models.DecimalField(max_digits=3, decimal_places=2)
    description = models.CharField(max_length=100, blank=True)
    
    class Meta:
        ordering = ['-min_percentage']
    
    def __str__(self):
        return f"{self.letter_grade} ({self.min_percentage}-{self.max_percentage}%)"

class Assignment(models.Model):
    """Model for assignments that can be graded"""
    course = models.ForeignKey(Subject, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    due_date = models.DateTimeField()
    max_points = models.DecimalField(max_digits=6, decimal_places=2, default=100.00)
    weight = models.DecimalField(max_digits=5, decimal_places=2, default=100.00, 
                                help_text="Weight in percentage for final grade")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'teacher'})
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.course.code} - {self.title}"

class AssignmentGrade(models.Model):
    """Grades for individual assignments"""
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'student'})
    points_earned = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    graded_at = models.DateTimeField(null=True, blank=True)
    feedback = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['assignment', 'student']
    
    def __str__(self):
        return f"{self.student.username} - {self.assignment.title}"
    
    def save(self, *args, **kwargs):
        if self.points_earned and self.assignment.max_points > 0:
            self.percentage = (self.points_earned / self.assignment.max_points) * 100
        super().save(*args, **kwargs)

class GradeReport(models.Model):
    """Model for grade reports and statistics"""
    course = models.ForeignKey(Subject, on_delete=models.CASCADE)
    report_type = models.CharField(max_length=50, choices=[
        ('semester', 'Semester Report'),
        ('midterm', 'Midterm Report'),
        ('final', 'Final Report'),
        ('custom', 'Custom Report')
    ])
    generated_by = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role__in': ['admin', 'teacher', 'registrar']})
    generated_at = models.DateTimeField(auto_now_add=True)
    report_data = models.JSONField(default=dict)  # Store report statistics
    average_grade = models.DecimalField(max_digits=4, decimal_places=2, default=0.00)
    highest_grade = models.DecimalField(max_digits=4, decimal_places=2, default=0.00)
    lowest_grade = models.DecimalField(max_digits=4, decimal_places=2, default=0.00)
    
    def __str__(self):
        return f"{self.course.code} - {self.report_type} Report"
    
    def generate_report_data(self):
        """Generate statistical data for the report"""
        grades = Grade.objects.filter(course=self.course)
        grade_points = []
        
        for grade in grades:
            if grade.grade:
                grade_points.append(grade.get_grade_point())
        
        if grade_points:
            self.average_grade = sum(grade_points) / len(grade_points)
            self.highest_grade = max(grade_points)
            self.lowest_grade = min(grade_points)
        
        # Store grade distribution
        grade_distribution = {}
        for grade in grades:
            if grade.grade:
                letter_grade = grade.grade.upper()
                grade_distribution[letter_grade] = grade_distribution.get(letter_grade, 0) + 1
        
        self.report_data = {
            'total_students': grades.count(),
            'graded_students': len([g for g in grades if g.grade]),
            'grade_distribution': grade_distribution,
            'grade_points_data': grade_points
        }
        
        self.save()