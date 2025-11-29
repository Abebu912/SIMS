from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from subjects.models import Subject

User = get_user_model()

class Grade(models.Model):
    """Numeric score model for primary students. Keeps compatibility by exposing
    a `grade` property (letter) and `get_grade_point()` helper used in views.
    """
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'student'})
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    # overall numeric score (0-100)
    score = models.PositiveIntegerField(null=True, blank=True, help_text='Numeric score out of 100')
    # component scores (new fields) - note: migrations required after this change
    quiz_score = models.PositiveIntegerField(null=True, blank=True, help_text='Quiz score (max 5)')
    mid_score = models.PositiveIntegerField(null=True, blank=True, help_text='Midterm score (max 25)')
    assignment_score = models.PositiveIntegerField(null=True, blank=True, help_text='Assignment score (max 20)')
    final_exam_score = models.PositiveIntegerField(null=True, blank=True, help_text='Final exam score (max 50)')
    remarks = models.TextField(blank=True)
    graded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['student', 'subject']

    def __str__(self):
        return f"{self.student.username} - {self.subject.code}: {self.score}"

    @property
    def grade(self):
        """Return a letter grade derived from numeric score for compatibility."""
        if self.score is None:
            return None
        s = self.score
        if s >= 90:
            return 'A'
        if s >= 80:
            return 'B'
        if s >= 70:
            return 'C'
        if s >= 60:
            return 'D'
        return 'F'

    def get_grade_point(self):
        letter = self.grade
        mapping = {
            'A': 4.0, 'A-': 3.7,
            'B+': 3.3, 'B': 3.0, 'B-': 2.7,
            'C+': 2.3, 'C': 2.0, 'C-': 1.7,
            'D+': 1.3, 'D': 1.0, 'D-': 0.7,
            'F': 0.0
        }
        return mapping.get((letter or '').upper(), 0.0)

    # Compatibility aliases for older code that used `course`, `credits`, and `grade` fields
    @property
    def course(self):
        return self.subject

    @property
    def credits(self):
        return getattr(self.subject, 'credit_hours', 0) or 0

    @property
    def result(self):
        """Numeric result alias for templates that expect `result` or `score` name."""
        return self.score


class Transcript(models.Model):
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
        grades = Grade.objects.filter(student=self.student)
        total_points = 0
        total_credits = 0
        for g in grades:
            if g.score is not None:
                # assume each subject has credit_hours attribute
                credits = getattr(g.subject, 'credit_hours', 0) or 0
                total_points += g.get_grade_point() * credits
                total_credits += credits

        if total_credits > 0:
            self.gpa = total_points / total_credits
            self.total_credits = total_credits
        else:
            self.gpa = 0.00
            self.total_credits = 0

        self.save()
        return self.gpa


def calculate_student_average(student, academic_year=None, semester=None):
    """Compute the weighted average numeric score for a student across subjects.
    If academic_year/semester provided, filter enrollments or grades accordingly (if such fields exist).
    """
    qs = Grade.objects.filter(student=student)
    # If filtering by academic_year/semester is desired and Grades store such info, add filters here.
    total_points = 0.0
    total_credits = 0
    for g in qs.select_related('subject'):
        if g.score is None:
            continue
        credits = getattr(g.subject, 'credit_hours', 0) or 0
        total_points += g.score * credits
        total_credits += credits
    if total_credits == 0:
        return None
    # Return average as numeric out of 100
    return total_points / total_credits


def rank_students_for_subject(subject, academic_year=None, semester=None):
    """Return list of (student, score, rank) ordered by score desc for a given subject."""
    qs = Grade.objects.filter(subject=subject).select_related('student')
    # optionally filter by academic_year/semester
    scored = [g for g in qs if g.score is not None]
    scored.sort(key=lambda x: x.score, reverse=True)
    results = []
    last_score = None
    last_rank = 0
    idx = 0
    for g in scored:
        idx += 1
        if g.score == last_score:
            rank = last_rank
        else:
            rank = idx
            last_rank = rank
            last_score = g.score
        results.append((g.student, g.score, rank))
    return results

