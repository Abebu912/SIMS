from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.utils import timezone
from .models import User, StudentProfile, TeacherProfile, ParentProfile, StudentParent, RegistrarProfile, FinanceProfile
import re
import datetime

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email'}))
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter first name'}))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter last name'}))
    role = forms.ChoiceField(choices=User.ROLE_CHOICES, widget=forms.Select(attrs={'class': 'form-control', 'id': 'role-select'}))
    phone = forms.CharField(max_length=15, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter phone number'}))
    date_of_birth = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    
    # Student-specific fields
    grade_level = forms.ChoiceField(
        choices=StudentProfile.GRADE_CHOICES,
        required=False,
        help_text="Required for students",
        widget=forms.Select(attrs={'class': 'form-control role-specific', 'id': 'id_grade_level'})
    )
    def _build_academic_year_choices():
        now = datetime.datetime.now()
        choices = []
        # generate a small range of academic years around current
        start = now.year - 2
        for y in range(start, start + 6):
            choices.append((f"{y}-{y+1}", f"{y}-{y+1}"))
        return choices

    academic_year = forms.ChoiceField(
        choices=_build_academic_year_choices(),
        required=False,
        initial=None,
        help_text="Required for students (select academic year)",
        widget=forms.Select(attrs={'class': 'form-control role-specific', 'id': 'id_academic_year'})
    )
    current_semester = forms.ChoiceField(
        choices=StudentProfile.SEMESTER_CHOICES,
        required=False,
        initial='first',
        help_text="Required for students",
        widget=forms.Select(attrs={'class': 'form-control role-specific', 'id': 'id_current_semester'})
    )
    
    # Teacher-specific fields
    department = forms.CharField(
        max_length=100, 
        required=False, 
        help_text="Required for teachers",
        widget=forms.TextInput(attrs={'class': 'form-control role-specific', 'placeholder': 'e.g., Mathematics Department', 'id': 'id_department'})
    )
    qualification = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control role-specific', 'rows': 3, 'placeholder': 'Enter your qualifications...', 'id': 'id_qualification'}), 
        required=False, 
        help_text="Required for teachers"
    )
    
    # Parent-specific fields
    occupation = forms.CharField(
        max_length=100, 
        required=False, 
        help_text="Required for parents",
        widget=forms.TextInput(attrs={'class': 'form-control role-specific', 'placeholder': 'e.g., Engineer, Doctor, Business', 'id': 'id_occupation'})
    )
    relationship = forms.ChoiceField(
        choices=[
            ('Father', 'Father'),
            ('Mother', 'Mother'),
            ('Guardian', 'Guardian'),
            ('Other', 'Other')
        ],
        required=False,
        help_text="Required for parents",
        widget=forms.Select(attrs={'class': 'form-control role-specific', 'id': 'id_relationship'})
    )
    student_id_link = forms.CharField(
        max_length=20,
        required=False,
        help_text="Optional: Link to existing student ID (for parents)",
        widget=forms.TextInput(attrs={'class': 'form-control role-specific', 'placeholder': 'Enter student ID to link', 'id': 'id_student_id_link'})
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'role', 'phone', 
                 'date_of_birth', 'password1', 'password2', 'grade_level', 'academic_year',
                 'current_semester', 'department', 'qualification', 'occupation', 'relationship', 'student_id_link']
        
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Choose a username'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter password'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm password'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hide all role-specific fields initially
        role_specific_fields = ['grade_level', 'academic_year', 'current_semester', 'department', 'qualification', 'occupation', 'relationship', 'student_id_link']
        for field_name in role_specific_fields:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs['style'] = 'display: none;'
    
    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        
        # Role-specific validation
        if role == 'student':
            if not cleaned_data.get('grade_level'):
                raise forms.ValidationError("Grade level is required for students.")
            if not cleaned_data.get('academic_year'):
                raise forms.ValidationError("Academic year is required for students.")
            if not cleaned_data.get('current_semester'):
                raise forms.ValidationError("Semester is required for students.")
            
            # Validate academic year format
            academic_year = cleaned_data.get('academic_year')
            if academic_year and not re.match(r'^\d{4}-\d{4}$', academic_year):
                raise forms.ValidationError("Academic year must be in format YYYY-YYYY (e.g., 2024-2025)")
        
        elif role == 'teacher':
            if not cleaned_data.get('department'):
                raise forms.ValidationError("Department is required for teachers.")
            if not cleaned_data.get('qualification'):
                raise forms.ValidationError("Qualification is required for teachers.")
        
        elif role == 'parent':
            if not cleaned_data.get('occupation'):
                raise forms.ValidationError("Occupation is required for parents.")
            if not cleaned_data.get('relationship'):
                raise forms.ValidationError("Relationship is required for parents.")
        
        # Validate student linking for parents
        if role == 'parent' and cleaned_data.get('student_id_link'):
            student_id = cleaned_data.get('student_id_link').strip()
            try:
                student = User.objects.get(
                    studentprofile__student_id=student_id,
                    role='student'
                )
                if StudentParent.objects.filter(parent__username=cleaned_data.get('username'), student=student).exists():
                    raise forms.ValidationError(f"You are already linked to student {student_id}.")
            except User.DoesNotExist:
                raise forms.ValidationError(f"Student with ID {student_id} not found. Please check the ID or leave blank.")
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_approved = False
        
        if commit:
            user.save()
            
            role = self.cleaned_data.get('role')
            
            if role == 'student':
                StudentProfile.objects.create(
                    user=user,
                    grade_level=self.cleaned_data.get('grade_level'),
                    academic_year=self.cleaned_data.get('academic_year'),
                    current_semester=self.cleaned_data.get('current_semester', 'first')
                )
            
            elif role == 'teacher':
                TeacherProfile.objects.create(
                    user=user,
                    department=self.cleaned_data.get('department', 'General'),
                    qualification=self.cleaned_data.get('qualification', ''),
                    hire_date=timezone.now().date()
                )
            
            elif role == 'parent':
                parent_profile = ParentProfile.objects.create(
                    user=user,
                    parent_id=f"PAR{user.id:06d}",
                    occupation=self.cleaned_data.get('occupation', ''),
                    relationship=self.cleaned_data.get('relationship', 'Parent')
                )
                
                student_id_link = self.cleaned_data.get('student_id_link')
                if student_id_link:
                    try:
                        student = User.objects.get(
                            studentprofile__student_id=student_id_link.strip(),
                            role='student'
                        )
                        StudentParent.objects.create(
                            parent=user,
                            student=student,
                            relationship=self.cleaned_data.get('relationship', 'Parent'),
                            is_primary=True
                        )
                    except User.DoesNotExist:
                        pass
        
        return user

class UserLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Enter your username',
            'autocomplete': 'username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password'
        })
    )

class AdminUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    role = forms.ChoiceField(choices=User.ROLE_CHOICES, widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_role'}))
    phone = forms.CharField(max_length=15, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    is_approved = forms.BooleanField(initial=True, required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    
    # Student-specific fields
    grade_level = forms.ChoiceField(
        choices=StudentProfile.GRADE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_grade_level'})
    )
    # academic_year should be selectable based on standard academic calendar
    def _build_admin_academic_year_choices():
        now = datetime.datetime.now()
        choices = []
        start = now.year - 2
        for y in range(start, start + 6):
            choices.append((f"{y}-{y+1}", f"{y}-{y+1}"))
        return choices

    academic_year = forms.ChoiceField(
        choices=_build_admin_academic_year_choices(),
        required=False,
        initial=None,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_academic_year'})
    )
    current_semester = forms.ChoiceField(
        choices=StudentProfile.SEMESTER_CHOICES,
        required=False,
        initial='first',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # Teacher-specific fields
    department = forms.CharField(
        max_length=100, 
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Mathematics Department'})
    )
    qualification = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter qualifications...'})
    )
    
    # Parent-specific fields
    occupation = forms.CharField(
        max_length=100, 
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Engineer, Doctor'})
    )
    relationship = forms.ChoiceField(
        choices=[
            ('Father', 'Father'),
            ('Mother', 'Mother'),
            ('Guardian', 'Guardian'),
            ('Other', 'Other')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    student_id_link = forms.CharField(
        max_length=20,
        required=False,
        help_text="Optional: Link to existing student ID (for parents)",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter student ID to link'})
    )
    
    # Registrar-specific fields
    office = forms.CharField(
        max_length=100,
        required=False,
        initial='Registrar Office',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Registrar Office'})
    )
    
    # Finance-specific fields
    finance_id = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., FIN001'})
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'role', 'phone', 
                 'is_approved', 'password1', 'password2', 'grade_level', 'academic_year',
                 'current_semester', 'department', 'qualification', 'occupation', 'relationship', 
                 'student_id_link', 'office', 'finance_id']
        
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['is_approved'].initial = True
    
    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        
        if role == 'student':
            if not cleaned_data.get('grade_level'):
                self.add_error('grade_level', 'Grade level is required for students.')
            if not cleaned_data.get('academic_year'):
                self.add_error('academic_year', 'Academic year is required for students.')
            if not cleaned_data.get('current_semester'):
                self.add_error('current_semester', 'Semester is required for students.')
            
            academic_year = cleaned_data.get('academic_year')
            if academic_year and not re.match(r'^\d{4}-\d{4}$', academic_year):
                self.add_error('academic_year', 'Academic year must be in format YYYY-YYYY (e.g., 2024-2025)')
        
        elif role == 'teacher':
            if not cleaned_data.get('department'):
                self.add_error('department', 'Department is required for teachers.')
            if not cleaned_data.get('qualification'):
                self.add_error('qualification', 'Qualification is required for teachers.')
        
        elif role == 'parent':
            if not cleaned_data.get('occupation'):
                self.add_error('occupation', 'Occupation is required for parents.')
            if not cleaned_data.get('relationship'):
                self.add_error('relationship', 'Relationship is required for parents.')
        
        elif role == 'registrar':
            if not cleaned_data.get('office'):
                self.add_error('office', 'Office is required for registrar.')
        
        elif role == 'finance':
            if not cleaned_data.get('finance_id'):
                self.add_error('finance_id', 'Finance ID is required for finance officers.')
        
        if role == 'parent' and cleaned_data.get('student_id_link'):
            student_id = cleaned_data.get('student_id_link').strip()
            try:
                student = User.objects.get(
                    studentprofile__student_id=student_id,
                    role='student'
                )
                if StudentParent.objects.filter(parent__username=cleaned_data.get('username'), student=student).exists():
                    self.add_error('student_id_link', f"You are already linked to student {student_id}.")
            except User.DoesNotExist:
                self.add_error('student_id_link', f"Student with ID {student_id} not found. Please check the ID or leave blank.")
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_approved = self.cleaned_data.get('is_approved', True)
        
        if commit:
            user.save()
            
            role = self.cleaned_data.get('role')
            
            if role == 'student':
                StudentProfile.objects.create(
                    user=user,
                    grade_level=self.cleaned_data.get('grade_level'),
                    academic_year=self.cleaned_data.get('academic_year'),
                    current_semester=self.cleaned_data.get('current_semester', 'first')
                )
            
            elif role == 'teacher':
                TeacherProfile.objects.create(
                    user=user,
                    department=self.cleaned_data.get('department', 'General'),
                    qualification=self.cleaned_data.get('qualification', ''),
                    hire_date=timezone.now().date()
                )
            
            elif role == 'parent':
                parent_profile = ParentProfile.objects.create(
                    user=user,
                    parent_id=f"PAR{user.id:06d}",
                    occupation=self.cleaned_data.get('occupation', ''),
                    relationship=self.cleaned_data.get('relationship', 'Parent')
                )
                
                student_id_link = self.cleaned_data.get('student_id_link')
                if student_id_link:
                    try:
                        student = User.objects.get(
                            studentprofile__student_id=student_id_link.strip(),
                            role='student'
                        )
                        StudentParent.objects.create(
                            parent=user,
                            student=student,
                            relationship=self.cleaned_data.get('relationship', 'Parent'),
                            is_primary=True
                        )
                    except User.DoesNotExist:
                        pass
            
            elif role == 'registrar':
                RegistrarProfile.objects.create(
                    user=user,
                    office=self.cleaned_data.get('office', 'Registrar Office')
                )
            
            elif role == 'finance':
                FinanceProfile.objects.create(
                    user=user,
                    finance_id=self.cleaned_data.get('finance_id', f"FIN{user.id:06d}")
                )
        
        return user

# Keep other form classes as they are...
class ProfileCompletionForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'date_of_birth', 'address', 'profile_picture']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class SystemSettingsForm(forms.Form):
    site_name = forms.CharField(max_length=100, initial='Student Information Management System', widget=forms.TextInput(attrs={'class': 'form-control'}))
    site_description = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}), required=False, initial='A comprehensive student information management system')
    enable_registration = forms.BooleanField(initial=True, required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    require_approval = forms.BooleanField(initial=True, required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    max_courses_per_student = forms.IntegerField(initial=5, min_value=1, max_value=20, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    grade_scale = forms.ChoiceField(choices=[('4.0', '4.0 Scale (A=4.0, B=3.0, etc)'), ('100', '100 Point Scale'), ('letter', 'Letter Grades Only')], initial='4.0', widget=forms.Select(attrs={'class': 'form-control'}))
    
    def clean_max_courses_per_student(self):
        max_courses = self.cleaned_data.get('max_courses_per_student')
        if max_courses < 1:
            raise forms.ValidationError("Maximum courses per student must be at least 1.")
        return max_courses

class AnnouncementForm(forms.Form):
    title = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter announcement title'}))
    content = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Enter announcement content'}))
    target_roles = forms.MultipleChoiceField(choices=User.ROLE_CHOICES, required=False, widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}), help_text="Select which roles should see this announcement (leave empty for all)")
    is_active = forms.BooleanField(initial=True, required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}), help_text="Show this announcement to users")