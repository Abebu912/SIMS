from django import forms
from .models import Grade

class GradeForm(forms.ModelForm):
    GRADE_CHOICES = [
        ('', 'Select Grade'),
        ('A', 'A (Excellent)'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B', 'B (Good)'),
        ('B-', 'B-'),
        ('C+', 'C+'),
        ('C', 'C (Average)'),
        ('C-', 'C-'),
        ('D+', 'D+'),
        ('D', 'D (Below Average)'),
        ('D-', 'D-'),
        ('F', 'F (Fail)'),
    ]
    
    grade = forms.ChoiceField(choices=GRADE_CHOICES, required=False)
    remarks = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter any remarks about student performance...'}),
        required=False
    )
    
    class Meta:
        model = Grade
        fields = ['grade', 'remarks']