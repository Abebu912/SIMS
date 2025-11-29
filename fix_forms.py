# fix_forms.py
import os

def fix_forms():
    print("🔧 Adding SystemSettingsForm to users/forms.py...")
    
    # The complete forms.py content is too long to include here
    # Instead, we'll just add the missing SystemSettingsForm
    
    # Read current forms.py
    with open('users/forms.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add SystemSettingsForm at the end if it doesn't exist
    if 'class SystemSettingsForm' not in content:
        system_settings_form = '''
class SystemSettingsForm(forms.Form):
    """Form for system settings configuration"""
    site_name = forms.CharField(
        max_length=100,
        initial='Student Information Management System',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    site_description = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False,
        initial='A comprehensive student information management system'
    )
    enable_registration = forms.BooleanField(
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    require_approval = forms.BooleanField(
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    max_courses_per_student = forms.IntegerField(
        initial=5,
        min_value=1,
        max_value=20,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    grade_scale = forms.ChoiceField(
        choices=[
            ('4.0', '4.0 Scale (A=4.0, B=3.0, etc)'),
            ('100', '100 Point Scale'),
            ('letter', 'Letter Grades Only')
        ],
        initial='4.0',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def clean_max_courses_per_student(self):
        max_courses = self.cleaned_data.get('max_courses_per_student')
        if max_courses < 1:
            raise forms.ValidationError("Maximum courses per student must be at least 1.")
        return max_courses
'''
        
        # Add the form at the end of the file
        content += system_settings_form
    
    # Write back
    with open('users/forms.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ SystemSettingsForm added successfully!")

if __name__ == '__main__':
    fix_forms()