from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import User, StudentProfile, TeacherProfile
from .forms import UserRegistrationForm, UserLoginForm

def role_required(*roles):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if request.user.is_authenticated and request.user.role in roles:
                return view_func(request, *args, **kwargs)
            messages.error(request, "You don't have permission to access this page.")
            return redirect('dashboard')
        return wrapper
    return decorator

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_approved = False  # Need admin approval
            user.save()
            
            # Create profile based on role
            if user.role == 'student':
                StudentProfile.objects.create(
                    user=user,
                    student_id=f"STU{user.id:06d}",
                    program=form.cleaned_data.get('program', 'General'),
                    semester=1,
                    enrollment_date=timezone.now().date()
                )
            elif user.role == 'teacher':
                TeacherProfile.objects.create(
                    user=user,
                    department=form.cleaned_data.get('department', 'General'),
                    qualification=form.cleaned_data.get('qualification', ''),
                    hire_date=timezone.now().date()
                )
            
            messages.success(request, 'Registration successful! Please wait for admin approval.')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'registration/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None and user.is_approved:
                login(request, user)
                messages.success(request, f'Welcome back, {user.username}!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid credentials or account not approved.')
    else:
        form = UserLoginForm()
    return render(request, 'registration/login.html', {'form': form})

@login_required
def dashboard(request):
    context = {
        'total_students': User.objects.filter(role='student', is_approved=True).count(),
        'total_teachers': User.objects.filter(role='teacher', is_approved=True).count(),
        'total_courses': Course.objects.filter(is_active=True).count() if 'courses' in apps.all_models else 0,
        'pending_approvals': User.objects.filter(is_approved=False).count(),
    }
    return render(request, 'dashboard.html', context)