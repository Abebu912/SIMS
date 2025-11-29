from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from .decorators import admin_required
from .models import User, StudentProfile, TeacherProfile
from courses.models import Course
from notifications.models import Announcement
from .forms import UserCreationForm, SystemSettingsForm

@admin_required
def admin_panel(request):
    # Admin statistics
    stats = {
        'total_users': User.objects.count(),
        'pending_approvals': User.objects.filter(is_approved=False).count(),
        'active_courses': Course.objects.filter(is_active=True).count(),
        'recent_registrations': User.objects.order_by('-date_joined')[:5],
    }
    
    context = {
        'stats': stats,
        'pending_users': User.objects.filter(is_approved=False),
    }
    return render(request, 'admin/admin_panel.html', context)

@admin_required
def manage_users(request):
    users = User.objects.all().select_related('studentprofile', 'teacherprofile')
    
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        action = request.POST.get('action')
        user = get_object_or_404(User, id=user_id)
        
        if action == 'approve':
            user.is_approved = True
            user.save()
            messages.success(request, f'User {user.username} has been approved.')
        elif action == 'delete':
            user.delete()
            messages.success(request, f'User {user.username} has been deleted.')
        elif action == 'toggle_active':
            user.is_active = not user.is_active
            user.save()
            status = 'activated' if user.is_active else 'deactivated'
            messages.success(request, f'User {user.username} has been {status}.')
        
        return redirect('manage_users')
    
    context = {
        'users': users,
    }
    return render(request, 'admin/manage_users.html', context)

@admin_required
def add_user(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_approved = True  # Auto-approve admin-created users
            user.save()
            
            # Create profile based on role
            if user.role == 'student':
                StudentProfile.objects.create(
                    user=user,
                    student_id=f"STU{user.id:06d}",
                    program=form.cleaned_data.get('program', 'General'),
                    semester=1
                )
            elif user.role == 'teacher':
                TeacherProfile.objects.create(
                    user=user,
                    department=form.cleaned_data.get('department', 'General'),
                    qualification=form.cleaned_data.get('qualification', ''),
                )
            
            messages.success(request, f'User {user.username} created successfully!')
            return redirect('manage_users')
    else:
        form = UserCreationForm()
    
    context = {
        'form': form,
    }
    return render(request, 'admin/add_user.html', context)

@admin_required
def system_settings(request):
    if request.method == 'POST':
        form = SystemSettingsForm(request.POST)
        if form.is_valid():
            # Here you would typically save settings to database or config file
            messages.success(request, 'System settings updated successfully!')
            return redirect('system_settings')
    else:
        form = SystemSettingsForm()
    
    context = {
        'form': form,
    }
    return render(request, 'admin/system_settings.html', context)

@admin_required
def generate_reports(request):
    reports = {
        'user_breakdown': User.objects.values('role').annotate(count=Count('id')),
        'registration_trends': User.objects.extra(
            select={'month': "strftime('%%Y-%%m', date_joined)"}
        ).values('month').annotate(count=Count('id')).order_by('month'),
    }
    
    if request.method == 'POST':
        report_type = request.POST.get('report_type')
        # Generate specific report logic here
        messages.success(request, f'{report_type} report generated successfully!')
    
    context = {
        'reports': reports,
    }
    return render(request, 'admin/generate_reports.html', context)

@admin_required
def post_announcement(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        target_roles = request.POST.getlist('target_roles')
        
        announcement = Announcement.objects.create(
            title=title,
            content=content,
            created_by=request.user,
            target_roles=target_roles
        )
        
        messages.success(request, 'Announcement posted successfully!')
        return redirect('admin_panel')
    
    context = {
        'role_choices': User.ROLE_CHOICES,
    }
    return render(request, 'admin/post_announcement.html', context)