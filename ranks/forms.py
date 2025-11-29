from django import forms
from .models import Grade

class GradeForm(forms.ModelForm):
    # component fields
    quiz_score = forms.IntegerField(min_value=0, max_value=5, required=False, label='Quiz (out of 5)')
    mid_score = forms.IntegerField(min_value=0, max_value=25, required=False, label='Mid (out of 25)')
    assignment_score = forms.IntegerField(min_value=0, max_value=20, required=False, label='Assignment (out of 20)')
    final_exam_score = forms.IntegerField(min_value=0, max_value=50, required=False, label='Final (out of 50)')
    score = forms.IntegerField(min_value=0, max_value=100, required=False, label='Total (0-100)')
    remarks = forms.CharField(widget=forms.Textarea(attrs={'rows':3}), required=False)

    class Meta:
        model = Grade
        fields = ['quiz_score', 'mid_score', 'assignment_score', 'final_exam_score', 'score', 'remarks']
