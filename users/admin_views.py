from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from .decorators import admin_required
from .models import User, StudentProfile, TeacherProfile
from subjects.models import Subject
from notifications.models import Announcement
from notifications.models import Notification
from .forms import UserCreationForm, SystemSettingsForm
from .forms import AdminUserCreationForm 
from django.utils import timezone 
from django.core.mail import send_mail, EmailMultiAlternatives, get_connection
from django.conf import settings
import json, os
from notifications.models import Notification
from django.urls import reverse
@login_required
def admin_panel(request):
    """Admin panel view"""
    if not request.user.is_superuser and getattr(request.user, 'role', None) != 'admin':
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
    # Admin statistics - handle missing tables gracefully
    try:
        total_subjects = Subject.objects.filter(is_active=True).count()
    except Exception:
        total_subjects = 0  # Default value if subjects table doesn't exist
    
    stats = {
        'total_users': User.objects.count(),
        'pending_approvals': User.objects.filter(is_approved=False).count(),
        'total_subjects': total_subjects,
        'recent_registrations': User.objects.order_by('-date_joined')[:5],
    }
    
    context = {
        'stats': stats,
        'pending_users': User.objects.filter(is_approved=False),
        'notifications': Notification.objects.filter(user=request.user).order_by('-created_at')[:10],
    }
    return render(request, 'admin/admin_panel.html', context)

@login_required
def manage_users(request):
    """Manage users view for admin"""
    if not request.user.is_superuser and getattr(request.user, 'role', None) != 'admin':
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
    users = User.objects.all().select_related('studentprofile', 'teacherprofile', 'parentprofile', 'registrarprofile', 'financeprofile')
    
    # Calculate statistics
    active_users_count = users.filter(is_active=True).count()
    pending_approvals_count = users.filter(is_approved=False).count()
    recent_users_count = users.filter(date_joined__gte=timezone.now() - timezone.timedelta(days=7)).count()
    
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        action = request.POST.get('action')
        user = get_object_or_404(User, id=user_id)
        
        if action == 'approve':
            user.is_approved = True
            user.save()
            messages.success(request, f'User {user.username} has been approved.')
        elif action == 'disapprove':
            user.is_approved = False
            user.save()
            messages.warning(request, f'User {user.username} has been disapproved.')
        elif action == 'activate':
            user.is_active = True
            user.save()
            messages.success(request, f'User {user.username} has been activated.')
        elif action == 'deactivate':
            user.is_active = False
            user.save()
            messages.warning(request, f'User {user.username} has been deactivated.')
        elif action == 'delete':
            username = user.username
            user.delete()
            messages.success(request, f'User {username} has been deleted.')
        
        return redirect('manage_users')
    
    context = {
        'users': users,
        'active_users_count': active_users_count,
        'pending_approvals_count': pending_approvals_count,
        'recent_users_count': recent_users_count,
    }
    return render(request, 'admin/manage_users.html', context)
@login_required
def add_user(request):
    """Add user view for admin"""
    print("=== ADD USER VIEW CALLED ===")
    
    # Check if user is admin
    if not request.user.is_superuser and getattr(request.user, 'role', None) != 'admin':
        messages.error(request, "You don't have permission to access this page.")
        print("REDIRECT: User doesn't have admin permissions")
        return redirect('dashboard')
    
    if request.method == 'POST':
        print("POST request received")
        form = AdminUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'User {user.username} created successfully!')
            return redirect('manage_users')
        else:
            print("Form errors:", form.errors)
            messages.error(request, 'Please correct the errors below.')
    else:
        print("GET request - creating new form")
        form = AdminUserCreationForm()
    
    print("Rendering template: admin/add_user.html")
    context = {'form': form}
    return render(request, 'admin/add_user.html', context)

@login_required
def system_settings(request):
    """System settings view for admin"""
    if not request.user.is_superuser and getattr(request.user, 'role', None) != 'admin':
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
    base_dir = getattr(settings, 'BASE_DIR', os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    site_settings_path = os.path.join(base_dir, 'site_settings.json')
    site_settings = {}
    if os.path.exists(site_settings_path):
        try:
            with open(site_settings_path, 'r', encoding='utf-8') as f:
                site_settings = json.load(f)
        except json.JSONDecodeError:
            messages.warning(request, 'site_settings.json is malformed. Using default values until it is fixed.')
            site_settings = {}
    
    email_cfg = site_settings.get('email') or site_settings.get('email_settings') or {}
    default_from_email = (
        site_settings.get('default_from_email')
        or email_cfg.get('default_from_email')
        or getattr(settings, 'DEFAULT_FROM_EMAIL', '')
    )
    
    if request.method == 'POST':
        action = request.POST.get('action', 'save')
        
        # Extract common settings from the POST body (form fields)
        site_name = request.POST.get('site_name', '').strip() or 'Student Information Management System'
        site_description = request.POST.get('site_description', '').strip() or ''
        admin_email = request.POST.get('admin_email', '').strip() or None
        # Other optional settings
        enable_user_registration = bool(request.POST.get('enable_user_registration'))
        require_admin_approval = bool(request.POST.get('require_admin_approval'))
        require_email_verification = bool(request.POST.get('require_email_verification'))
        max_login_attempts = int(request.POST.get('max_login_attempts') or site_settings.get('max_login_attempts') or 5)
        max_courses_per_student = int(request.POST.get('max_courses_per_student') or site_settings.get('max_courses_per_student') or 6)
        grade_scale = request.POST.get('grade_scale') or site_settings.get('grade_scale') or '4.0'
        passing_grade = int(request.POST.get('passing_grade') or site_settings.get('passing_grade') or 60)
        auto_backup_frequency = request.POST.get('backup_frequency') or site_settings.get('auto_backup_frequency') or 'weekly'
        session_timeout = int(request.POST.get('session_timeout') or site_settings.get('session_timeout') or 30)
        
        default_from_email = (
            request.POST.get('default_from_email', '').strip()
            or default_from_email
            or admin_email
            or getattr(settings, 'DEFAULT_FROM_EMAIL', '')
        )
        
        email_backend = request.POST.get('email_backend', '').strip() or email_cfg.get('backend') or getattr(settings, 'EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
        email_host = request.POST.get('email_host', '').strip() or email_cfg.get('host') or getattr(settings, 'EMAIL_HOST', '')
        email_port_raw = request.POST.get('email_port', '').strip() or email_cfg.get('port')
        try:
            email_port = int(email_port_raw) if email_port_raw not in (None, '') else None
        except ValueError:
            email_port = None
        email_host_user = request.POST.get('email_host_user', '').strip() or email_cfg.get('user') or default_from_email
        email_host_password = request.POST.get('email_host_password', '')
        if not email_host_password:
            email_host_password = email_cfg.get('password', '') or getattr(settings, 'EMAIL_HOST_PASSWORD', '')
        email_use_tls = bool(request.POST.get('email_use_tls'))
        email_use_ssl = bool(request.POST.get('email_use_ssl'))

        # Persist settings to a simple JSON file so they survive restarts
        site_settings.update({
            'site_name': site_name,
            'site_description': site_description,
            'admin_email': admin_email,
            'enable_user_registration': enable_user_registration,
            'require_admin_approval': require_admin_approval,
            'require_email_verification': require_email_verification,
            'max_login_attempts': max_login_attempts,
            'max_courses_per_student': max_courses_per_student,
            'grade_scale': grade_scale,
            'passing_grade': passing_grade,
            'auto_backup_frequency': auto_backup_frequency,
            'session_timeout': session_timeout,
            'default_from_email': default_from_email,
            'email': {
                'backend': email_backend,
                'host': email_host,
                'port': email_port,
                'user': email_host_user,
                'password': email_host_password,
                'use_tls': email_use_tls,
                'use_ssl': email_use_ssl,
                'default_from_email': default_from_email,
            }
        })
        # Maintain backwards compatibility with older loaders
        site_settings['email_settings'] = site_settings['email']
        
        try:
            with open(site_settings_path, 'w', encoding='utf-8') as f:
                json.dump(site_settings, f, indent=2)
        except Exception as exc:
            messages.error(request, f'Failed to persist settings file: {exc}')

        # Update runtime settings where appropriate (ADMINS and DEFAULT_FROM_EMAIL)
        try:
            if admin_email:
                settings.ADMINS = [("Site Admin", admin_email)]
            if default_from_email:
                settings.DEFAULT_FROM_EMAIL = default_from_email
            settings.EMAIL_BACKEND = email_backend
            settings.EMAIL_HOST = email_host
            if email_port is not None:
                settings.EMAIL_PORT = email_port
            settings.EMAIL_HOST_USER = email_host_user
            if email_host_password:
                settings.EMAIL_HOST_PASSWORD = email_host_password
            settings.EMAIL_USE_TLS = email_use_tls
            settings.EMAIL_USE_SSL = email_use_ssl
        except Exception:
            pass

        # Create an announcement so admins will see the change on dashboards
        try:
            ann = Announcement.objects.create(
                title='System settings updated',
                content=f"System settings were updated by {request.user.get_full_name() or request.user.username}.",
                created_by=request.user,
                target_roles=['admin']
            )
        except Exception:
            ann = None

        # Create a Notification for admin users so they see it on their dashboard immediately
        try:
            admin_users = User.objects.filter(role='admin')
            if not admin_users.exists():
                admin_users = User.objects.filter(is_staff=True)
            for u in admin_users:
                Notification.objects.create(
                    user=u,
                    title='System settings updated',
                    message=f'System settings were updated by {request.user.get_full_name() or request.user.username}.',
                    link='/users/system-settings/'
                )
        except Exception:
            pass

        if action == 'send_test_email':
            test_email = request.POST.get('test_email_recipient', '').strip()
            if not test_email:
                messages.error(request, 'Enter a recipient email address to send the test message.')
            else:
                try:
                    connection = get_connection(
                        backend=settings.EMAIL_BACKEND,
                        host=settings.EMAIL_HOST or None,
                        port=settings.EMAIL_PORT or None,
                        username=settings.EMAIL_HOST_USER or None,
                        password=getattr(settings, 'EMAIL_HOST_PASSWORD', None),
                        use_tls=settings.EMAIL_USE_TLS,
                        use_ssl=settings.EMAIL_USE_SSL,
                    )
                    send_mail(
                        'SIMS email configuration test',
                        'This is a test email from the Student Information Management System. If you received this, SMTP settings are working.',
                        settings.DEFAULT_FROM_EMAIL,
                        [test_email],
                        connection=connection,
                        fail_silently=False,
                    )
                    messages.success(request, f'Test email sent to {test_email}.')
                except Exception as exc:
                    messages.error(request, f'Failed to send test email: {exc}')
        else:
            messages.success(request, 'System settings updated successfully!')
        return redirect('system_settings')
    
    # You can pass initial data to the template if needed
    email_settings_context = {
        'backend': email_cfg.get('backend') or getattr(settings, 'EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend'),
        'host': email_cfg.get('host') or getattr(settings, 'EMAIL_HOST', ''),
        'port': email_cfg.get('port') or getattr(settings, 'EMAIL_PORT', ''),
        'user': email_cfg.get('user') or getattr(settings, 'EMAIL_HOST_USER', ''),
        'use_tls': email_cfg.get('use_tls') if email_cfg.get('use_tls') is not None else getattr(settings, 'EMAIL_USE_TLS', True),
        'use_ssl': email_cfg.get('use_ssl') if email_cfg.get('use_ssl') is not None else getattr(settings, 'EMAIL_USE_SSL', False),
        'has_password': bool(email_cfg.get('password')),
    }
    context = {
        'site_settings': site_settings,
        'email_settings': email_settings_context,
        'default_from_email': default_from_email or getattr(settings, 'DEFAULT_FROM_EMAIL', ''),
        'email_backends': [
            ('django.core.mail.backends.smtp.EmailBackend', 'SMTP (Recommended)'),
            ('django.core.mail.backends.console.EmailBackend', 'Console (Development)'),
            ('django.core.mail.backends.filebased.EmailBackend', 'File-based (Development)'),
        ],
    }
    return render(request, 'admin/system_settings.html', context)

@login_required
def generate_reports(request):
    """Generate reports view for admin"""
    if not request.user.is_superuser and getattr(request.user, 'role', None) != 'admin':
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
    # You can pass report data to the template
    from django.db.models import Count
    reports = {
        'user_breakdown': User.objects.values('role').annotate(count=Count('id')),
    }
    
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
        # Create Notification objects and send emails to targeted users
        try:
            if target_roles:
                recipients_qs = User.objects.filter(role__in=target_roles)
            else:
                recipients_qs = User.objects.all()

            # Filter out users without email
            recipients = recipients_qs.exclude(email='').values_list('email', flat=True)

            # Send email individually to each recipient (sends a plain text and HTML part).
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@localhost')
            site_name = getattr(settings, 'SITE_NAME', None) or ''
            for email in recipients:
                try:
                    subject = title
                    text_content = content + "\n\n" + f"Posted {announcement.created_at.strftime('%b %d, %Y %H:%M')}"
                    html_content = f"<html><body><p>{content}</p><hr><p>Posted {announcement.created_at.strftime('%b %d, %Y %H:%M')}</p></body></html>"
                    msg = EmailMultiAlternatives(subject, text_content, from_email, [email])
                    msg.attach_alternative(html_content, "text/html")
                    # Send (will use SMTP if configured in settings, otherwise console backend)
                    msg.send(fail_silently=True)
                except Exception as exc:
                    # log to console — don't stop processing other recipients
                    print(f"Failed sending announcement to {email}: {exc}")

            # Also create Notification entries for in-app notifications
            for u in recipients_qs:
                try:
                    Notification.objects.create(
                        user=u,
                        title=title,
                        message=content,
                        link=reverse('view_announcements') if 'reverse' in globals() else '/users/announcements/'
                    )
                except Exception:
                    pass
        except Exception:
            pass

        messages.success(request, 'Announcement posted successfully!')
        return redirect('admin_panel')
    
    context = {
        'role_choices': User.ROLE_CHOICES,
    }
    return render(request, 'admin/post_announcement.html', context)
# Add this to admin_views.py
def debug_add_user(request):
    """Debug view to see what's happening"""
    from .forms import AdminUserCreationForm
    
    print("=== DEBUG ADD USER ===")
    print("Request method:", request.method)
    print("User:", request.user)
    print("User is authenticated:", request.user.is_authenticated)
    print("User role:", getattr(request.user, 'role', 'No role'))
    print("User is superuser:", request.user.is_superuser)
    
    form = AdminUserCreationForm()
    print("Form fields:", list(form.fields.keys()))
    
    context = {
        'form': form,
        'debug_info': f"User: {request.user}, Role: {getattr(request.user, 'role', 'None')}"
    }
    return render(request, 'admin/add_user.html', context)