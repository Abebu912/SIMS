from django import forms

class ClaimSubjectForm(forms.Form):
    subject_id = forms.IntegerField(widget=forms.HiddenInput)

class ScoreEntryForm(forms.Form):
    student_id = forms.IntegerField(widget=forms.HiddenInput)
    score = forms.IntegerField(min_value=0, max_value=100, required=False)
    result = forms.CharField(max_length=50, required=False)

class BulkScoreUploadForm(forms.Form):
    grade_file = forms.FileField(required=True)

class BulkAssignForm(forms.Form):
    grade_level = forms.IntegerField(min_value=1, max_value=12)
    academic_year = forms.CharField(max_length=9)
    semester = forms.ChoiceField(choices=[('first','First'),('second','Second')])
