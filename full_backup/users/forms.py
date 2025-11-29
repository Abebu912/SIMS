from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.utils import timezone
from .models import User, StudentProfile, TeacherProfile, ParentProfile, StudentParent

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email'}))
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter first name'}))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter last name'}))
    role = forms.ChoiceField(choices=User.ROLE_CHOICES, widget=forms.Select(attrs={'class': 'form-control', 'id': 'role-select'}))
    phone = forms.CharField(max_length=15, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter phone number'}))
    date_of_birth = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    
    # Additional fields for specific roles
    program = forms.CharField(
        max_length=100, 
        required=False, 
        help_text="Required for students",
        widget=forms.TextInput(attrs={'class': 'form-control role-specific', 'placeholder': 'e.g., Computer Science'})
    )
    department = forms.CharField(
        max_length=100, 
        required=False, 
        help_text="Required for teachers",
        widget=forms.TextInput(attrs={'class': 'form-control role-specific', 'placeholder': 'e.g., Mathematics Department'})
    )
    qualification = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control role-specific', 'rows': 3, 'placeholder': 'Enter your qualifications...'}), 
        required=False, 
        help_text="Required for teachers"
    )
    occupation = forms.CharField(
        max_length=100, 
        required=False, 
        help_text="Required for parents",
        widget=forms.TextInput(attrs={'class': 'form-control role-specific', 'placeholder': 'e.g., Engineer, Doctor, Business'})
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
        widget=forms.Select(attrs={'class': 'form-control role-specific'})
    )
    student_id_link = forms.CharField(
        max_length=20,
        required=False,
        help_text="Optional: Link to existing student ID (for parents)",
        widget=forms.TextInput(attrs={'class': 'form-control role-specific', 'placeholder': 'Enter student ID to link'})
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'role', 'phone', 
                 'date_of_birth', 'password1', 'password2']
        
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Choose a username'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter password'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm password'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add CSS classes to role-specific fields for JavaScript handling
        for field_name, field in self.fields.items():
            if hasattr(field, 'widget') and hasattr(field.widget, 'attrs'):
                if field_name in ['program', 'department', 'qualification', 'occupation', 'relationship', 'student_id_link']:
                    field.widget.attrs['class'] = field.widget.attrs.get('class', '') + ' role-specific'
                    field.widget.attrs['style'] = 'display: none;'  # Hide initially
    
    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        
        # Role-specific validation
        if role == 'student' and not cleaned_data.get('program'):
            raise forms.ValidationError("Program is required for students.")
        
        if role == 'teacher':
            if not cleaned_data.get('department'):
                raise forms.ValidationError("Department is required for teachers.")
            if not cleaned_data.get('qualification'):
                raise forms.ValidationError("Qualification is required for teachers.")
        
        if role == 'parent':
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
                # Check if this parent is already linked to this student
                if StudentParent.objects.filter(parent__username=cleaned_data.get('username'), student=student).exists():
                    raise forms.ValidationError(f"You are already linked to student {student_id}.")
            except User.DoesNotExist:
                raise forms.ValidationError(f"Student with ID {student_id} not found. Please check the ID or leave blank.")
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_approved = False  # Need admin approval for all new registrations
        
        if commit:
            user.save()
            
            # Create profile based on role
            role = self.cleaned_data.get('role')
            
            if role == 'student':
                StudentProfile.objects.create(
                    user=user,
                    student_id=f"STU{user.id:06d}",
                    program=self.cleaned_data.get('program', 'General'),
                    semester=1,
                    enrollment_date=timezone.now().date()
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
                
                # Link to student if provided
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
                        # Student not found, but we still create the parent profile
                        pass
            
            elif role == 'registrar':
                # Registrar profile can be added here if needed
                pass
            
            elif role == 'finance':
                # Finance profile can be added here if needed
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
    """Form for admin to create users with immediate approval"""
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    role = forms.ChoiceField(choices=User.ROLE_CHOICES)
    phone = forms.CharField(max_length=15, required=False)
    is_approved = forms.BooleanField(initial=True, required=False)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'role', 'phone', 'is_approved', 'password1', 'password2']
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_approved = self.cleaned_data.get('is_approved', True)
        
        if commit:
            user.save()
            
            # Create appropriate profile
            role = self.cleaned_data.get('role')
            if role == 'student':
                StudentProfile.objects.create(
                    user=user,
                    student_id=f"STU{user.id:06d}",
                    program='General',
                    semester=1,
                    enrollment_date=timezone.now().date()
                )
            elif role == 'teacher':
                TeacherProfile.objects.create(
                    user=user,
                    department='General',
                    qualification='',
                    hire_date=timezone.now().date()
                )
            elif role == 'parent':
                ParentProfile.objects.create(
                    user=user,
                    parent_id=f"PAR{user.id:06d}",
                    occupation='',
                    relationship='Parent'
                )
        
        return user

class UserUpdateForm(forms.ModelForm):
    """Form for users to update their profile"""
    phone = forms.CharField(max_length=15, required=False)
    date_of_birth = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'date_of_birth', 'profile_picture']

class ParentStudentLinkForm(forms.ModelForm):
    """Form for parents to link additional students"""
    student_id = forms.CharField(
        max_length=20,
        required=True,
        help_text="Enter the student ID to link to your account"
    )
    relationship = forms.ChoiceField(
        choices=[
            ('Father', 'Father'),
            ('Mother', 'Mother'),
            ('Guardian', 'Guardian'),
            ('Other', 'Other')
        ],
        required=True
    )
    
    class Meta:
        model = StudentParent
        fields = ['relationship']
    
    def clean_student_id(self):
        student_id = self.cleaned_data.get('student_id').strip()
        try:
            student = User.objects.get(
                studentprofile__student_id=student_id,
                role='student'
            )
            return student
        except User.DoesNotExist:
            raise forms.ValidationError(f"Student with ID {student_id} not found. Please check the ID.")
    
    def clean(self):
        cleaned_data = super().clean()
        student = cleaned_data.get('student_id')
        relationship = cleaned_data.get('relationship')
        
        if student and self.instance.parent:
            # Check if already linked
            if StudentParent.objects.filter(parent=self.instance.parent, student=student).exists():
                raise forms.ValidationError(f"You are already linked to student {student.studentprofile.student_id}.")
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.student = self.cleaned_data['student_id']
        
        if commit:
            instance.save()
        
        return instance

class ProfileCompletionForm(forms.ModelForm):
    """Form for users to complete their profile after registration"""
    
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