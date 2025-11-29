from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q, Count
from collections import defaultdict
from django.apps import apps
from django.http import HttpResponse, JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import User, StudentProfile, TeacherProfile, ParentProfile, StudentParent
from subjects.models import Subject, Enrollment
from payments.models import Payment
from notifications.models import Announcement, Notification
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView
from django.conf import settings

# Import forms
try:
    from .forms import UserRegistrationForm, UserLoginForm, AdminUserCreationForm
except ImportError:
    UserRegistrationForm = None
    UserLoginForm = None
    AdminUserCreationForm = None

class CustomPasswordResetView(PasswordResetView):
    template_name = 'registration/password_reset.html'
    email_template_name = 'registration/password_reset_email.html'
    subject_template_name = 'registration/password_reset_subject.txt'
    html_email_template_name = 'registration/password_reset_email_html.html'
    
    def form_valid(self, form):
        messages.info(self.request, "If an account with that email exists, reset instructions have been sent.")
        return super().form_valid(form)

class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'registration/password_reset_done.html'

def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f'Account created successfully! Welcome, {user.first_name}!')
                return redirect('dashboard')
            else:
                messages.success(request, f'Account created successfully! Please wait for admin approval.')
                return redirect('login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'registration/register.html', {'form': form})

@login_required
def dashboard_view(request):
    context = {
        'user': request.user,
    }
    return render(request, 'registration/dashboard.html', context)

def custom_login_view(request):
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name}!')
            return redirect('dashboard')
    else:
        form = UserLoginForm()
    
    return render(request, 'registration/login.html', {'form': form})

@login_required
def protected_home(request):
    return redirect('dashboard')

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

def user_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_approved = False
            user.save()
            
            # Create profile based on role - UPDATED for grade system
            if user.role == 'student':
                student_profile = StudentProfile.objects.create(
                    user=user,
                    grade_level=form.cleaned_data.get('grade_level', 1),
                    academic_year=form.cleaned_data.get('academic_year', '2024-2025'),
                    current_semester='first'
                )
                # Auto-enroll student into default/core subjects for their grade
                try:
                    grade_lvl = student_profile.grade_level
                    ay = student_profile.academic_year or get_current_academic_year()
                    sem = student_profile.current_semester or get_current_semester()
                    enrolled_count, failures = enroll_student_in_default_subjects(user, grade_lvl, academic_year=ay, semester=sem, status='pending')
                    if enrolled_count > 0:
                        messages.info(request, f'Auto-registered {enrolled_count} core subject(s) for Grade {grade_lvl}.')
                    if failures:
                        for subj, reason in failures:
                            if subj is None:
                                messages.warning(request, f'Auto-enrollment issue: {reason}')
                            else:
                                messages.warning(request, f'Could not auto-enroll {subj.name}: {reason}')
                except Exception:
                    # Do not break registration on auto-enroll failures
                    pass
            elif user.role == 'teacher':
                TeacherProfile.objects.create(
                    user=user,
                    department=form.cleaned_data.get('department', 'General'),
                    qualification=form.cleaned_data.get('qualification', ''),
                    hire_date=timezone.now().date()
                )
            elif user.role == 'parent':
                parent_profile = ParentProfile.objects.create(
                    user=user,
                    parent_id=f"PAR{user.id:06d}",
                    occupation=form.cleaned_data.get('occupation', ''),
                    relationship=form.cleaned_data.get('relationship', 'Parent')
                )
                
                student_id_link = form.cleaned_data.get('student_id_link')
                if student_id_link:
                    try:
                        student = User.objects.get(
                            studentprofile__student_id=student_id_link.strip(),
                            role='student'
                        )
                        StudentParent.objects.create(
                            parent=user,
                            student=student,
                            relationship=form.cleaned_data.get('relationship', 'Parent'),
                            is_primary=True
                        )
                    except User.DoesNotExist:
                        pass
            
            messages.success(request, 'Registration successful! Please wait for admin approval.')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'registration/register.html', {'form': form})

# API Token Views
@api_view(['POST'])
def obtain_auth_token(request):
    return Response({
        'message': 'Token endpoint - implement with your authentication system',
        'token': 'placeholder-token'
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
def refresh_auth_token(request):
    return Response({
        'message': 'Token refresh endpoint - implement with your authentication system',
        'token': 'placeholder-refreshed-token'
    }, status=status.HTTP_200_OK)

# Dashboard and Main Views
@login_required
def dashboard(request):
    user = request.user
    
    total_students = User.objects.filter(role='student', is_approved=True).count()
    total_teachers = User.objects.filter(role='teacher', is_approved=True).count()
    
    # Count active subjects (formerly called courses)
    total_subjects = Subject.objects.filter(is_active=True).count()
    
    pending_approvals = User.objects.filter(is_approved=False).count()
    
    # Get unread notifications for the user
    unread_notifications = Notification.objects.filter(user=user, is_read=False).order_by('-created_at')[:5]
    unread_count = Notification.objects.filter(user=user, is_read=False).count()
    
    context = {
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_subjects': total_subjects,
        'pending_approvals': pending_approvals,
        'unread_notifications': unread_notifications,
        'unread_count': unread_count,
    }
    
    return render(request, 'dashboard.html', context)

@login_required
def view_subjects(request):
    if not hasattr(request.user, 'studentprofile'):
        messages.error(request, "This page is only available for students.")
        return redirect('dashboard')
    
    subjects = [
        {'name': 'Mathematics', 'teacher': 'Mr. Smith', 'schedule': 'Mon, Wed 9:00 AM'},
        {'name': 'English', 'teacher': 'Ms. Johnson', 'schedule': 'Tue, Thu 10:00 AM'},
        {'name': 'Science', 'teacher': 'Dr. Brown', 'schedule': 'Mon, Fri 11:00 AM'},
        {'name': 'Social Studies', 'teacher': 'Mrs. Davis', 'schedule': 'Tue, Thu 1:00 PM'},
    ]
    
    context = {
        'subjects': subjects,
    }
    return render(request, 'students/view_subjects.html', context)

@login_required
def view_ranks(request):
    if not hasattr(request.user, 'studentprofile'):
        messages.error(request, "This page is only available for students.")
        return redirect('dashboard')
    
    ranks = [
        {'subject': 'Mathematics', 'rank': '1', 'score': '95'},
        {'subject': 'English', 'rank': '2', 'score': '88'},
        {'subject': 'Science', 'rank': '1', 'score': '92'},
        {'subject': 'Social Studies', 'rank': '3', 'score': '85'},
    ]
    
    context = {
        'ranks': ranks,
    }
    return render(request, 'students/view_ranks.html', context)

@login_required
def view_homework(request):
    if not hasattr(request.user, 'studentprofile'):
        messages.error(request, "This page is only available for students.")
        return redirect('dashboard')
    
    homework_list = [
        {'subject': 'Mathematics', 'title': 'Chapter 5 Exercises', 'due_date': '2024-12-20', 'status': 'Pending'},
        {'subject': 'English', 'title': 'Essay Writing', 'due_date': '2024-12-18', 'status': 'Completed'},
        {'subject': 'Science', 'title': 'Lab Report', 'due_date': '2024-12-22', 'status': 'Pending'},
    ]
    
    context = {
        'homework_list': homework_list,
        'pending_count': len([h for h in homework_list if h['status'] == 'Pending'])
    }
    return render(request, 'students/view_homework.html', context)

@login_required
def interact_with_ai(request):
    return render(request, 'students/ai_assistant.html')

@login_required
def view_announcements(request):
    announcements = [
        {'title': 'School Holiday', 'content': 'School will be closed on December 25th for Christmas.', 'date': '2024-12-20'},
        {'title': 'Parent-Teacher Meeting', 'content': 'Parent-teacher meetings scheduled for next week.', 'date': '2024-12-15'},
        {'title': 'Sports Day', 'content': 'Annual sports day will be held on December 30th.', 'date': '2024-12-10'},
    ]
    
    context = {
        'announcements': announcements
    }
    return render(request, 'announcements/view_announcements.html', context)

# users/views.py - UPDATE THIS VIEW
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from subjects.models import Subject, Enrollment, ScheduleConflict, Teacher
import datetime
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError

# ADD: Helper functions
def get_current_academic_year():
    now = datetime.datetime.now()
    if now.month >= 8:  # Academic year starts in August
        return f"{now.year}-{now.year + 1}"
    else:
        return f"{now.year - 1}-{now.year}"

def get_current_semester():
    now = datetime.datetime.now()
    # Simplify semester mapping to the two-semester model (first/second)
    if now.month >= 8:
        return 'first'  # Fall semester
    else:
        return 'second'  # Spring/remaining months treated as second


def enroll_student_in_default_subjects(student_user, grade_level, academic_year=None, semester=None, status='pending'):
    """Auto-enroll a student into default/core subjects for their grade.

    - Enrolls only subjects with subject_type='core' and is_active=True for the given grade_level.
    - Creates Enrollment objects with provided academic_year and semester (defaults to current)
    - Returns a tuple: (enrolled_count, failures) where failures is list of (subject, reason)
    """
    from django.core.exceptions import ValidationError
    from django.db import IntegrityError

    if academic_year is None:
        academic_year = get_current_academic_year()
    if semester is None:
        semester = get_current_semester()

    enrolled_count = 0
    failures = []

    # Use configurable subject types from settings
    subject_types = getattr(settings, 'AUTO_ENROLL_SUBJECT_TYPES', ['core'])
    try:
        subjects_qs = Subject.objects.filter(
            grade_level=grade_level,
            is_active=True,
            subject_type__in=subject_types
        ).order_by('code')
        # Deduplicate subjects by name (case-insensitive). Prefer first occurrence (ordered by code).
        subjects = []
        seen = set()
        for s in subjects_qs:
            key = (s.name or '').strip().lower()
            if key and key not in seen:
                subjects.append(s)
                seen.add(key)
    except Exception as e:
        return (0, [(None, f'Failed to load subjects: {e}')])

    for subj in subjects:
        try:
            # skip if enrollment already exists for this student/subject/term
            existing = Enrollment.objects.filter(
                student=student_user,
                subject=subj,
                academic_year=academic_year,
                semester=semester
            ).first()
            if existing:
                continue
            
            # Also skip if the student is already enrolled in a subject with the same name
            name_conflict = Enrollment.objects.filter(
                student=student_user,
                subject__name__iexact=subj.name,
                academic_year=academic_year,
                semester=semester,
                status__in=('active','approved')
            ).exists()
            if name_conflict:
                # avoid enrolling duplicate subject names (different subject records)
                continue

            Enrollment.objects.create(
                student=student_user,
                subject=subj,
                academic_year=academic_year,
                semester=semester,
                status=status,
                is_auto_assigned=True
            )
            enrolled_count += 1
        except ValidationError as ve:
            failures.append((subj, '; '.join(ve.messages) if hasattr(ve, 'messages') else str(ve)))
        except IntegrityError as ie:
            failures.append((subj, str(ie)))
        except Exception as e:
            failures.append((subj, str(e)))

    return (enrolled_count, failures)

def check_schedule_conflicts(student, selected_subjects, academic_year, semester):
    """
    Check for scheduling conflicts between selected subjects
    """
    conflicts = []
    
    # Get subjects with schedule information
    scheduled_subjects = [s for s in selected_subjects if s.day_of_week and s.start_time and s.end_time]
    
    # Group by day and check for time conflicts
    days_schedule = {}
    for subject in scheduled_subjects:
        if subject.day_of_week not in days_schedule:
            days_schedule[subject.day_of_week] = []
        days_schedule[subject.day_of_week].append(subject)
    
    # Check for time conflicts on each day
    for day, subjects in days_schedule.items():
        # Sort by start time
        subjects.sort(key=lambda x: x.start_time)
        
        for i in range(len(subjects)):
            for j in range(i + 1, len(subjects)):
                subject1 = subjects[i]
                subject2 = subjects[j]
                
                # Check if times overlap
                if (subject1.start_time < subject2.end_time and 
                    subject1.end_time > subject2.start_time):
                    
                    conflicts.append({
                        'subject1': subject1,
                        'subject2': subject2,
                        'day': subject1.get_day_of_week_display() if hasattr(subject1, 'get_day_of_week_display') else subject1.day_of_week,
                        'time1': f"{subject1.start_time.strftime('%H:%M')} - {subject1.end_time.strftime('%H:%M')}",
                        'time2': f"{subject2.start_time.strftime('%H:%M')} - {subject2.end_time.strftime('%H:%M')}",
                    })
    
    return conflicts

LETTER_GRADE_TO_SCORE = {
    'A+': 98,
    'A': 95,
    'A-': 92,
    'B+': 88,
    'B': 85,
    'B-': 82,
    'C+': 78,
    'C': 75,
    'C-': 72,
    'D+': 68,
    'D': 65,
    'D-': 62,
    'F': 55,
}


def letter_grade_to_numeric(letter):
    """Map letter grades to an elementary-friendly 100 point scale."""
    if not letter:
        return None
    return LETTER_GRADE_TO_SCORE.get(letter.strip().upper())


def compute_numeric_scores(student, enrollments):
    """
    Return a tuple of (score_map, total, count, average) for the given enrollments.
    score_map maps enrollment.id -> numeric score (0-100) or None.
    """
    subject_ids = [en.subject_id for en in enrollments if getattr(en, 'subject_id', None)]
    rank_scores = {}
    if RankGrade is not None and subject_ids:
        try:
            rank_scores = {
                rg.subject_id: rg.score
                for rg in RankGrade.objects.filter(student=student, subject_id__in=subject_ids)
            }
        except Exception:
            rank_scores = {}

    score_map = {}
    total = 0.0
    count = 0
    for enrollment in enrollments:
        score = rank_scores.get(enrollment.subject_id)
        if score is None:
            # First check enrollment.result field for numeric value
            result_val = getattr(enrollment, 'result', None)
            if result_val:
                try:
                    # Try to parse as numeric
                    score = float(result_val)
                except (ValueError, TypeError):
                    # If not numeric, fall back to letter grade conversion
                    score = letter_grade_to_numeric(getattr(enrollment, 'final_grade', None))
            else:
                # Fall back to letter grade conversion
                score = letter_grade_to_numeric(getattr(enrollment, 'final_grade', None))
        if score is not None:
            score = float(score)
            total += score
            count += 1
        score_map[enrollment.id] = score

    average = round(total / count, 2) if count else None
    return score_map, round(total, 2), count, average


def build_rank_map(entries):
    """
    entries: iterable of {'student_id': id, 'grade_level': grade, 'average': value}
    returns {student_id: rank}
    """
    grade_groups = defaultdict(list)
    for entry in entries:
        grade = entry.get('grade_level')
        avg = entry.get('average')
        student_id = entry.get('student_id')
        if grade is None or avg is None or student_id is None:
            continue
        grade_groups[grade].append((student_id, avg))

    rank_map = {}
    for grade, students in grade_groups.items():
        students.sort(key=lambda item: item[1], reverse=True)
        rank = 0
        previous = None
        for idx, (student_id, avg) in enumerate(students, start=1):
            if previous != avg:
                rank = idx
                previous = avg
            rank_map[student_id] = rank
    return rank_map

# users/views.py - UPDATE THE VIEW
@login_required
def subject_registration(request):
    if not hasattr(request.user, 'studentprofile'):
        messages.error(request, "This page is only available for students.")
        return redirect('dashboard')
    
    student_profile = request.user.studentprofile
    current_grade = student_profile.grade_level
    current_academic_year = get_current_academic_year()
    current_semester = get_current_semester()
    
    if request.method == 'POST':
        # Accept both 'subject_ids' and 'subject_ids[]' from different JS submitters
        subject_ids = request.POST.getlist('subject_ids') or request.POST.getlist('subject_ids[]')
        
        if subject_ids:
            # NEW: Get selected subjects with schedule info and filter by student's grade
            selected_subjects = Subject.objects.filter(
                id__in=subject_ids,
                is_active=True,
                grade_level=current_grade
            ).select_related('instructor', 'instructor__user')
            
            # NEW: Check for schedule conflicts
            conflicts = check_schedule_conflicts(
                request.user, 
                selected_subjects, 
                current_academic_year, 
                current_semester
            )
            
            # NEW: If conflicts found and user didn't force register, show warning
            if conflicts and 'force_register' not in request.POST:
                # Prepare context with conflict information
                available_subjects = Subject.objects.filter(
                    is_active=True,
                    grade_level=current_grade
                ).select_related('instructor', 'instructor__user').order_by('name')
                
                enrolled_subjects = Enrollment.objects.filter(
                    student=request.user,
                    academic_year=current_academic_year,
                    semester=current_semester,
                    status='active'
                ).select_related('subject', 'subject__instructor', 'subject__instructor__user')
                
                enrolled_subject_ids = [enrollment.subject.id for enrollment in enrolled_subjects]
                
                context = {
                    'available_subjects': available_subjects,
                    'enrolled_subjects': enrolled_subjects,
                    'enrolled_subject_ids': enrolled_subject_ids,
                    'current_grade': current_grade,
                    'current_academic_year': current_academic_year,
                    'current_semester': student_profile.get_current_semester_display(),
                    'selected_subject_ids': subject_ids,
                    'schedule_conflicts': conflicts,
                }
                return render(request, 'students/subject_registration.html', context)
            
            if not selected_subjects.exists():
                messages.error(request, "Selected subjects are not available for your grade level or are inactive.")
                return redirect('subject_registration')

            enrolled_count = 0
            failed = []
            with transaction.atomic():
                for subject in selected_subjects:
                    try:
                        # Check if student is already enrolled in this subject for current semester
                        existing_enrollment = Enrollment.objects.filter(
                            student=request.user, 
                            subject=subject,
                            academic_year=current_academic_year,
                            semester=current_semester
                        ).first()

                        if existing_enrollment:
                            if existing_enrollment.status in ('active', 'approved'):
                                messages.info(request, f"You are already enrolled in {subject.name} for {current_academic_year} {student_profile.get_current_semester_display()}.")
                            else:
                                # Reactivate dropped enrollment
                                existing_enrollment.status = 'active'
                                existing_enrollment.save()
                                enrolled_count += 1
                                messages.success(request, f"Re-enrolled in {subject.name}!")
                        else:
                            # Ensure subject grade level matches student's grade
                            try:
                                student_grade = getattr(student_profile, 'grade_level', None)
                            except Exception:
                                student_grade = None

                            if subject.grade_level != student_grade:
                                failed.append((subject, f"Subject is for Grade {subject.grade_level} but student is Grade {student_grade}"))
                                continue

                            # Check subject capacity
                            current_enrollment = subject.current_enrollment_count(current_academic_year, current_semester)

                            if current_enrollment < subject.max_capacity:
                                try:
                                    Enrollment.objects.create(
                                        student=request.user,
                                        subject=subject,
                                        academic_year=current_academic_year,
                                        semester=current_semester,
                                        status='active'
                                    )
                                    enrolled_count += 1
                                    messages.success(request, f"Successfully enrolled in {subject.name}!")
                                except ValidationError as ve:
                                    failed.append((subject, '; '.join(ve.messages) if hasattr(ve, 'messages') else str(ve)))
                                except IntegrityError as ie:
                                    failed.append((subject, str(ie)))
                            else:
                                messages.warning(request, f"Subject {subject.name} is full. Could not enroll.")
                                failed.append((subject, 'full'))
                    except Subject.DoesNotExist:
                        failed.append((subject, 'missing'))
                    except (IntegrityError, ValidationError) as e:
                        # Unique constraint or validation failed for this enrollment
                        failed.append((subject, str(e)))
            
            # NEW: Record schedule conflicts if any
            if conflicts:
                conflict_obj = ScheduleConflict.objects.create(
                    student=request.user,
                    academic_year=current_academic_year,
                    semester=current_semester
                )
                conflict_obj.conflicting_subjects.set([c['subject1'] for c in conflicts] + [c['subject2'] for c in conflicts])
                messages.warning(request, f'Registered {enrolled_count} subject(s) with schedule conflicts! Please review your schedule.')
            elif enrolled_count > 0:
                messages.success(request, f"Successfully enrolled in {enrolled_count} subject(s) for {current_academic_year} {student_profile.get_current_semester_display()}!")
            else:
                messages.info(request, "No new subjects were enrolled.")

            if failed:
                # Summarize failures
                for subj, reason in failed:
                    try:
                        name = subj.name
                    except Exception:
                        name = str(subj)
                    messages.error(request, f"Failed to enroll {name}: {reason}")
            
            return redirect('subject_registration')
    
    try:
        # UPDATED: Get available subjects with instructor and schedule info
        available_subjects = Subject.objects.filter(
            is_active=True,
            grade_level=current_grade
        ).select_related('instructor', 'instructor__user').order_by('name')
        
        # Get currently enrolled subjects for this academic year and semester
        enrolled_subjects = Enrollment.objects.filter(
            student=request.user,
            academic_year=current_academic_year,
            semester=current_semester,
            status='active'
        ).select_related('subject', 'subject__instructor', 'subject__instructor__user')
        
        enrolled_subject_ids = [enrollment.subject.id for enrollment in enrolled_subjects]
        
        # UPDATED: Deduplicate available subjects by name (case-insensitive) and add enhanced enrollment info
        deduped = []
        seen_names = set()
        for subject in available_subjects:
            key = (subject.name or '').strip().lower()
            if not key:
                continue
            if key in seen_names:
                continue
            # mark as seen and include
            seen_names.add(key)
            subject.current_enrollment = subject.current_enrollment_count(current_academic_year, current_semester)
            subject.available_slots = subject.available_slots(current_academic_year, current_semester)
            subject.is_available = subject.is_available(current_academic_year, current_semester)
            deduped.append(subject)
        available_subjects = deduped
            
    except Exception as e:
        print(f"Error in subject registration: {str(e)}")
        available_subjects = []
        enrolled_subjects = []
        enrolled_subject_ids = []
        messages.error(request, "Error loading subjects. Please try again later.")
    
    context = {
        'available_subjects': available_subjects,
        'enrolled_subjects': enrolled_subjects,
        'enrolled_subject_ids': enrolled_subject_ids,
        'current_grade': current_grade,
        'current_academic_year': current_academic_year,
        'current_semester': student_profile.get_current_semester_display(),
        'max_subjects': 8,
        'max_credits': 24,
    }
    # Support JSON responses for API/JS clients
    wants_json = (
        request.headers.get('Accept') == 'application/json'
        or request.content_type == 'application/json'
        or request.GET.get('format') == 'json'
    )

    if wants_json:
        enrolled_data = [{
            'enrollment_id': e.id,
            'subject_id': e.subject.id,
            'name': e.subject.name,
            'schedule': e.subject.schedule_display,
            'status': e.status,
            'final_grade': e.final_grade,
        } for e in enrolled_subjects]

        available_data = [{
            'id': s.id,
            'name': s.name,
            'grade_level': s.grade_level,
            'available_slots': s.available_slots,
            'schedule': s.schedule_display
        } for s in available_subjects]

        return JsonResponse({
            'current_grade': current_grade,
            'academic_year': current_academic_year,
            'semester': current_semester,
            'enrolled_subjects': enrolled_data,
            'available_subjects': available_data
        })

    return render(request, 'students/subject_registration.html', context)
@login_required
def view_transcripts(request):
    if not hasattr(request.user, 'studentprofile'):
        messages.error(request, "This page is only available for students.")
        return redirect('dashboard')
    
    student_profile = request.user.studentprofile
    context = {
        'student_profile': student_profile,
    }
    return render(request, 'students/view_transcripts.html', context)

@login_required
def pay_fees(request):
    context = {
        'outstanding_fees': 0,
    }
    return render(request, 'students/pay_fees.html', context)

@login_required
def student_dashboard(request):
    if request.user.role != 'student':
        messages.error(request, "You don't have permission to access the student dashboard.")
        return redirect('dashboard')
    
    try:
        student_profile = request.user.studentprofile
    except StudentProfile.DoesNotExist:
        messages.error(request, "Student profile not found. Please contact administration.")
        return redirect('dashboard')
    
    context = {
        'student_profile': student_profile,
        'enrolled_subjects': [
            {'name': 'Mathematics', 'teacher': 'Mr. Smith'},
            {'name': 'English', 'teacher': 'Ms. Johnson'},
            {'name': 'Science', 'teacher': 'Dr. Brown'},
        ],
        'average_grade': 'A-',
        'pending_homework': 3,
        'attendance_rate': 95,
        'completed_assignments': 15,
    }
    
    return render(request, 'students/student_dashboard.html', context)

@login_required
def edit_profile(request):
    user = request.user
    
    if request.method == 'POST':
        # Update basic user information
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.phone = request.POST.get('phone', user.phone)
        user.date_of_birth = request.POST.get('date_of_birth') or None
        user.address = request.POST.get('address', user.address)
        
        # Handle profile picture upload
        if 'profile_picture' in request.FILES:
            user.profile_picture = request.FILES['profile_picture']
        
        # Update role-specific profiles
        if user.role == 'student':
            try:
                student_profile = user.studentprofile
                student_profile.grade_level = request.POST.get('grade_level', student_profile.grade_level)
                student_profile.academic_year = request.POST.get('academic_year', student_profile.academic_year)
                student_profile.current_semester = request.POST.get('current_semester', student_profile.current_semester)
                student_profile.save()
            except StudentProfile.DoesNotExist:
                # Create student profile if it doesn't exist
                StudentProfile.objects.create(
                    user=user,
                    grade_level=request.POST.get('grade_level', 1),
                    academic_year=request.POST.get('academic_year', '2024-2025'),
                    current_semester=request.POST.get('current_semester', 'first')
                )
        
        elif user.role == 'teacher':
            try:
                teacher_profile = user.teacherprofile
                teacher_profile.department = request.POST.get('department', teacher_profile.department)
                teacher_profile.qualification = request.POST.get('qualification', teacher_profile.qualification)
                teacher_profile.save()
            except TeacherProfile.DoesNotExist:
                TeacherProfile.objects.create(
                    user=user,
                    department=request.POST.get('department', 'General'),
                    qualification=request.POST.get('qualification', '')
                )
        
        elif user.role == 'parent':
            try:
                parent_profile = user.parentprofile
                parent_profile.occupation = request.POST.get('occupation', parent_profile.occupation)
                parent_profile.relationship = request.POST.get('relationship', parent_profile.relationship)
                parent_profile.save()
            except ParentProfile.DoesNotExist:
                ParentProfile.objects.create(
                    user=user,
                    occupation=request.POST.get('occupation', ''),
                    relationship=request.POST.get('relationship', 'Parent')
                )
        
        try:
            user.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
        except Exception as e:
            messages.error(request, f'Error updating profile: {str(e)}')
    
    # Prepare context for the template
    context = {'user': user}
    
    # Add role-specific profiles to context
    if user.role == 'student':
        try:
            context['student_profile'] = user.studentprofile
        except StudentProfile.DoesNotExist:
            context['student_profile'] = None
    
    elif user.role == 'teacher':
        try:
            context['teacher_profile'] = user.teacherprofile
        except TeacherProfile.DoesNotExist:
            context['teacher_profile'] = None
    
    elif user.role == 'parent':
        try:
            context['parent_profile'] = user.parentprofile
            context['linked_students'] = StudentParent.objects.filter(parent=user).select_related('student', 'student__studentprofile')
        except ParentProfile.DoesNotExist:
            context['parent_profile'] = None
    
    return render(request, 'users/edit_profile.html', context)

@login_required
def profile(request):
    user = request.user
    context = {
        'user': user,
    }
    
    if user.role == 'student':
        try:
            context['student_profile'] = user.studentprofile
        except StudentProfile.DoesNotExist:
            pass
    elif user.role == 'teacher':
        try:
            context['teacher_profile'] = user.teacherprofile
        except TeacherProfile.DoesNotExist:
            pass
    elif user.role == 'parent':
        try:
            context['parent_profile'] = user.parentprofile
            context['linked_students'] = StudentParent.objects.filter(parent=user).select_related('student', 'student__studentprofile')
        except ParentProfile.DoesNotExist:
            pass
    
    return render(request, 'users/profile.html', context)
@login_required
def admin_panel(request):
    if not request.user.role == 'admin' and not request.user.is_superuser:
        messages.error(request, "You don't have permission to access the admin panel.")
        return redirect('dashboard')
    
    stats = {
        'total_users': User.objects.count(),
        'pending_approvals': User.objects.filter(is_approved=False).count(),
        'active_courses': Subject.objects.filter(is_active=True).count() if Subject else 0,
        'recent_registrations': User.objects.order_by('-date_joined')[:5],
    }
    
    context = {
        'stats': stats,
        'pending_users': User.objects.filter(is_approved=False),
    }
    return render(request, 'admin/admin_panel.html', context)

@login_required
def manage_users(request):
    if not request.user.role == 'admin' and not request.user.is_superuser:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
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

@login_required
def add_user(request):
    if not request.user.is_superuser and getattr(request.user, 'role', None) != 'admin':
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = AdminUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'User {user.username} created successfully!')
            return redirect('manage_users')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminUserCreationForm()
    
    context = {'form': form}
    return render(request, 'admin/add_user.html', context)

@login_required
def system_settings(request):
    if not request.user.role == 'admin' and not request.user.is_superuser:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
    messages.info(request, 'System settings functionality will be implemented here.')
    return render(request, 'admin/system_settings.html')

@login_required
def generate_reports(request):
    if not request.user.role == 'admin' and not request.user.is_superuser:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
    reports = {
        'user_breakdown': User.objects.values('role').annotate(count=Count('id')),
    }
    
    context = {
        'reports': reports,
    }
    return render(request, 'admin/generate_reports.html', context)

@login_required
def post_announcement(request):
    if not request.user.role == 'admin' and not request.user.is_superuser:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        target_roles = request.POST.getlist('target_roles')
        is_active = request.POST.get('is_active') == 'on'
        send_email = request.POST.get('send_email') == 'on'
        
        # Handle "all" option - if "all" is selected, use empty list (means show to everyone)
        if 'all' in target_roles:
            target_roles = []  # Empty list means show to all users
        
        announcement = Announcement.objects.create(
            title=title,
            content=content,
            created_by=request.user,
            target_roles=target_roles,
            is_active=is_active
        )
        
        # Get all users who should receive this announcement
        # If target_roles is empty (all selected), get all active users
        # Otherwise, filter by the selected roles
        if target_roles and len(target_roles) > 0:
            recipients = User.objects.filter(role__in=target_roles, is_active=True)
        else:
            # Empty list means all users
            recipients = User.objects.filter(is_active=True)
        
        # Create notifications and send emails
        notifications_created = 0
        emails_sent = 0
        emails_failed = 0
        
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@localhost')
        site_name = getattr(settings, 'SITE_NAME', 'SIMS')
        
        print(f"\n=== POSTING ANNOUNCEMENT ===")
        print(f"Title: {title}")
        print(f"Target roles: {target_roles}")
        print(f"Send email: {send_email}")
        print(f"Total recipients: {recipients.count()}")
        print(f"From email: {from_email}")
        
        for user in recipients:
            # Create notification for each user
            try:
                # Check if notification already exists to avoid duplicates
                notification, created = Notification.objects.get_or_create(
                    user=user,
                    title=title,
                    message=content,
                    defaults={'link': f'/announcements/'}
                )
                if created:
                    notifications_created += 1
            except Exception as e:
                print(f"Failed to create notification for {user.username}: {e}")
                import traceback
                traceback.print_exc()
            
            # Send email if requested and user has email
            if send_email:
                if not user.email:
                    print(f"⚠ User {user.username} has no email address, skipping email")
                    continue
                try:
                    subject = f"[{site_name}] {title}"
                    # Format content properly - replace newlines with <br> for HTML
                    formatted_content = content.replace('\n', '<br>').replace('\r', '')
                    text_content = f"{content}\n\nPosted on {announcement.created_at.strftime('%B %d, %Y at %H:%M')}\n\n---\n{site_name}"
                    html_content = f"""
                    <html>
                    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                            <h2 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">{title}</h2>
                            <div style="margin: 20px 0;">
                                {formatted_content}
                            </div>
                            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                            <p style="color: #7f8c8d; font-size: 12px;">
                                Posted on {announcement.created_at.strftime('%B %d, %Y at %H:%M')}<br>
                                ---<br>
                                {site_name}
                            </p>
                        </div>
                    </body>
                    </html>
                    """
                    msg = EmailMultiAlternatives(subject, text_content, from_email, [user.email])
                    msg.attach_alternative(html_content, "text/html")
                    # Try to send email - first with fail_silently=False to see errors
                    try:
                        result = msg.send(fail_silently=False)
                        emails_sent += 1
                        print(f"✓ Email sent successfully to {user.email} ({user.get_full_name()})")
                    except Exception as send_error:
                        emails_failed += 1
                        print(f"✗ SMTP Error sending to {user.email}: {send_error}")
                        # Try with fail_silently=True as fallback
                        try:
                            msg.send(fail_silently=True)
                            print(f"  (Retried silently)")
                        except:
                            pass
                except Exception as e:
                    emails_failed += 1
                    print(f"✗ Exception preparing email for {user.email}: {e}")
                    import traceback
                    traceback.print_exc()
        
        print(f"\n=== ANNOUNCEMENT POSTING SUMMARY ===")
        print(f"Notifications created: {notifications_created}")
        print(f"Emails sent: {emails_sent}")
        print(f"Emails failed: {emails_failed}")
        print(f"=====================================\n")
        
        success_msg = f'Announcement posted successfully!'
        if notifications_created > 0:
            success_msg += f' Notifications created: {notifications_created}.'
        if send_email:
            success_msg += f' Emails sent: {emails_sent}'
            if emails_failed > 0:
                success_msg += f' (Failed: {emails_failed} - check console/terminal for details)'
        
        messages.success(request, success_msg)
        return redirect('admin_panel')
    
    context = {
        'role_choices': User.ROLE_CHOICES,
    }
    return render(request, 'admin/post_announcement.html', context)
# users/views.py - ADD THIS FUNCTION
@login_required
def check_schedule_conflicts_ajax(request):
    """AJAX view to check schedule conflicts in real-time"""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            subject_ids = request.POST.getlist('subject_ids[]')
            
            if not subject_ids:
                return JsonResponse({'conflicts': [], 'has_conflicts': False})
            
            selected_subjects = Subject.objects.filter(
                id__in=subject_ids
            ).select_related('instructor', 'instructor__user')
            
            conflicts = check_schedule_conflicts(request.user, selected_subjects, '', '')
            
            conflict_data = []
            for conflict in conflicts:
                conflict_data.append({
                    'subject1_name': conflict['subject1'].name,
                    'subject1_code': conflict['subject1'].code,
                    'subject1_schedule': conflict['subject1'].schedule_display,
                    'subject2_name': conflict['subject2'].name,
                    'subject2_code': conflict['subject2'].code,
                    'subject2_schedule': conflict['subject2'].schedule_display,
                    'day': conflict['day'],
                    'time1': conflict['time1'],
                    'time2': conflict['time2'],
                })
            
            return JsonResponse({
                'conflicts': conflict_data,
                'has_conflicts': len(conflicts) > 0
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)
# users/views.py
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render

def is_registrar(user):
    """Check if user is a registrar"""
    return user.is_authenticated and user.role == 'registrar'

@login_required
@user_passes_test(is_registrar)
def registrar_dashboard(request):
    """Registrar dashboard view"""
    # Get unread notifications for the registrar
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')[:5]
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    
    context = {
        'page_title': 'Registrar Dashboard',
        'user': request.user,
        'unread_notifications': unread_notifications,
        'unread_count': unread_count,
    }
    return render(request, 'registrar/dashboard.html', context)
# users/views.py or registrar/views.py
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from subjects.models import Enrollment, Subject
from django.db.models import Q

def is_registrar(user):
    """Check if user is a registrar"""
    return user.is_authenticated and hasattr(user, 'role') and user.role == 'registrar'

@login_required
@user_passes_test(is_registrar)
def approve_registrations(request):
    """View pending registration approvals"""
    # Get pending enrollments
    pending_enrollments = Enrollment.objects.filter(
        status='pending'
    ).select_related('student', 'subject').order_by('-enrolled_date')
    
    # Get enrollment statistics
    stats = {
        'pending': pending_enrollments.count(),
        'approved': Enrollment.objects.filter(status='active').count(),
        'total_students': Enrollment.objects.values('student').distinct().count(),
    }
    
    context = {
        'page_title': 'Approve Registrations',
        'pending_enrollments': pending_enrollments,
        'stats': stats,
    }
    return render(request, 'registrar/approve_registrations.html', context)

@login_required
@user_passes_test(is_registrar)
def approve_single_registration(request, enrollment_id):
    """Approve a single registration"""
    enrollment = get_object_or_404(Enrollment, id=enrollment_id, status='pending')
    
    if request.method == 'POST':
        try:
            # Check if subject has available capacity
            current_enrollment = Enrollment.objects.filter(
                subject=enrollment.subject,
                academic_year=enrollment.academic_year,
                semester=enrollment.semester,
                status='active'
            ).count()
            
            if current_enrollment < enrollment.subject.max_capacity:
                enrollment.status = 'active'
                enrollment.approved_by = request.user
                enrollment.approved_date = timezone.now()
                enrollment.save()
                
                messages.success(request, f"Approved {enrollment.student.username}'s registration for {enrollment.subject.name}")
            else:
                messages.error(request, f"Cannot approve - {enrollment.subject.name} is full")
                
        except Exception as e:
            messages.error(request, f"Error approving registration: {str(e)}")
    
    return redirect('approve_registrations')

@login_required
@user_passes_test(is_registrar)
def reject_single_registration(request, enrollment_id):
    """Reject a single registration"""
    enrollment = get_object_or_404(Enrollment, id=enrollment_id, status='pending')
    
    if request.method == 'POST':
        enrollment.status = 'rejected'
        enrollment.approved_by = request.user
        enrollment.approved_date = timezone.now()
        enrollment.save()
        
        messages.warning(request, f"Rejected {enrollment.student.username}'s registration for {enrollment.subject.name}")
    
    return redirect('approve_registrations')

@login_required
@user_passes_test(is_registrar)
def bulk_approve_registrations(request):
    """Bulk approve multiple registrations"""
    if request.method == 'POST':
        enrollment_ids = request.POST.getlist('enrollment_ids')
        approved_count = 0
        
        for enrollment_id in enrollment_ids:
            try:
                enrollment = Enrollment.objects.get(id=enrollment_id, status='pending')
                
                # Check capacity
                current_enrollment = Enrollment.objects.filter(
                    subject=enrollment.subject,
                    academic_year=enrollment.academic_year,
                    semester=enrollment.semester,
                    status='active'
                ).count()
                
                if current_enrollment < enrollment.subject.max_capacity:
                    enrollment.status = 'active'
                    enrollment.approved_by = request.user
                    enrollment.approved_date = timezone.now()
                    enrollment.save()
                    approved_count += 1
                    
            except Enrollment.DoesNotExist:
                continue
        
        if approved_count > 0:
            messages.success(request, f"Approved {approved_count} registration(s)")
        else:
            messages.warning(request, "No registrations were approved")
    
    return redirect('approve_registrations')


@login_required
@user_passes_test(is_registrar)
def registrar_student_subjects(request, student_id):
    """Registrar view to display/manage a specific student's enrollments"""
    student = get_object_or_404(User, id=student_id, role='student')
    try:
        profile = student.studentprofile
    except StudentProfile.DoesNotExist:
        messages.error(request, 'Student profile not found')
        return redirect('manage_academic_records')

    year = get_current_academic_year()
    semester = get_current_semester()

    enrolled = Enrollment.objects.filter(
        student=student,
        academic_year=year,
        semester=semester
    ).select_related('subject', 'subject__instructor')

    available = Subject.objects.filter(
        is_active=True,
        grade_level=profile.grade_level
    ).exclude(id__in=[e.subject.id for e in enrolled]).order_by('code')

    context = {
        'student': student,
        'student_profile': profile,
        'enrolled_subjects': enrolled,
        'available_subjects': available,
        'current_year': year,
        'current_semester': semester,
    }
    return render(request, 'registrar/student_subjects.html', context)
# users/views.py
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q
from subjects.models import Enrollment, Grade
from django.db import OperationalError
try:
    from ranks.models import Grade as RankGrade
    from ranks.models import calculate_student_average, rank_students_for_subject
except Exception:
    RankGrade = None

@login_required
@user_passes_test(is_registrar)
def manage_academic_records(request):
    """Manage academic records for all students"""
    # Get filter parameters
    grade_level = request.GET.get('grade_level', '')
    academic_year = request.GET.get('academic_year', '')
    semester = request.GET.get('semester', '')
    
    # Get all students with their enrollments and annotate counts to avoid template queryset calls
    student_qs = User.objects.filter(role='student').annotate(
        total_enrollments=Count('subject_enrollments', distinct=True),
        completed_enrollments=Count('subject_enrollments', filter=Q(subject_enrollments__final_grade__isnull=False))
    ).prefetch_related(
        'subject_enrollments',
        'subject_enrollments__subject',
        'studentprofile'
    ).order_by('username')
    
    # Apply filters
    if grade_level:
        student_qs = student_qs.filter(studentprofile__grade_level=grade_level)
    
    if academic_year:
        student_qs = student_qs.filter(subject_enrollments__academic_year=academic_year)
    
    if semester:
        student_qs = student_qs.filter(subject_enrollments__semester=semester)
    
    students = list(student_qs)
    
    # Get unique values for filters
    grade_levels = StudentProfile.objects.values_list('grade_level', flat=True).distinct().order_by('grade_level')
    academic_years = Enrollment.objects.values_list('academic_year', flat=True).distinct().order_by('-academic_year')

    # Precompute GPA and total credits per student to simplify template rendering
    rank_entries = []
    for student in students:
        enrollment_manager = getattr(student, 'subject_enrollments', None)
        enrollments = list(enrollment_manager.all()) if enrollment_manager is not None else []
        score_map, total_result, graded_count, average_result = compute_numeric_scores(student, enrollments)
        student.result_total = total_result
        student.result_average = average_result
        student.graded_subjects = graded_count
        student.class_rank = None
        grade_level = getattr(getattr(student, 'studentprofile', None), 'grade_level', None)
        rank_entries.append({
            'student_id': student.id,
            'grade_level': grade_level,
            'average': average_result,
        })

    rank_map = build_rank_map(rank_entries)
    for student in students:
        student.class_rank = rank_map.get(student.id)
    
    context = {
        'page_title': 'Manage Academic Records',
        'students': students,
        'grade_levels': grade_levels,
        'academic_years': academic_years,
        'current_filters': {
            'grade_level': grade_level,
            'academic_year': academic_year,
            'semester': semester,
        }
    }
    return render(request, 'registrar/manage_academic_records.html', context)

@login_required
@user_passes_test(is_registrar)
def student_academic_record(request, student_id):
    """View detailed academic record for a specific student"""
    student = get_object_or_404(User, id=student_id, role='student')
    
    # Get all enrollments with grades
    enrollments = list(Enrollment.objects.filter(
        student=student
    ).select_related('subject').prefetch_related('grades').order_by('-academic_year', 'semester'))

    score_map, total_result, graded_count, result_average = compute_numeric_scores(student, enrollments)
    for enrollment in enrollments:
        enrollment.result_score = score_map.get(enrollment.id)
    
    class_rank = None
    grade_level = getattr(getattr(student, 'studentprofile', None), 'grade_level', None)
    if grade_level is not None:
        peers = list(
            User.objects.filter(role='student', studentprofile__grade_level=grade_level)
            .prefetch_related('subject_enrollments', 'subject_enrollments__subject', 'studentprofile')
        )
        rank_entries = []
        for peer in peers:
            enrollment_manager = getattr(peer, 'subject_enrollments', None)
            peer_enrollments = list(enrollment_manager.all()) if enrollment_manager is not None else []
            _, _, _, peer_average = compute_numeric_scores(peer, peer_enrollments)
            rank_entries.append({
                'student_id': peer.id,
                'grade_level': getattr(getattr(peer, 'studentprofile', None), 'grade_level', None),
                'average': peer_average,
            })
        rank_map = build_rank_map(rank_entries)
        class_rank = rank_map.get(student.id)
    
    context = {
        'page_title': f'Academic Record - {student.get_full_name()}',
        'student': student,
        'enrollments': enrollments,
        'result_total': total_result,
        'result_average': result_average,
        'graded_count': graded_count,
        'class_rank': class_rank,
    }
    return render(request, 'registrar/student_academic_record.html', context)

@login_required
@user_passes_test(is_registrar)
def update_grade(request, enrollment_id):
    """Update grade/score for a student's enrollment - accepts numerical values (0-100)"""
    enrollment = get_object_or_404(Enrollment, id=enrollment_id)
    
    if request.method == 'POST':
        grade_input = request.POST.get('final_grade', '').strip()
        
        if not grade_input:
            messages.error(request, "Please enter a score.")
            return redirect('student_academic_record', student_id=enrollment.student.id)
        
        # Try to parse as numeric score (0-100)
        try:
            score = float(grade_input)
            # Clamp score to valid range
            if score < 0:
                score = 0
            elif score > 100:
                score = 100
            
            # Update RankGrade if available
            if RankGrade is not None:
                grade_obj, created = RankGrade.objects.get_or_create(
                    student=enrollment.student,
                    subject=enrollment.subject,
                    defaults={'score': int(score)}
                )
                if not created:
                    grade_obj.score = int(score)
                    grade_obj.save()
            
            # Store numeric score in enrollment.result field
            enrollment.result = str(int(score))
            # Also store in final_grade for backward compatibility (as string representation)
            enrollment.final_grade = str(int(score))
            enrollment.save()
            
            messages.success(request, f"Updated score for {enrollment.student.username} in {enrollment.subject.name} to {int(score)}")
        except ValueError:
            messages.error(request, "Invalid score. Please enter a numerical value between 0 and 100.")
    
    return redirect('student_academic_record', student_id=enrollment.student.id)

@login_required
@user_passes_test(is_registrar)
def generate_transcript(request, student_id):
    """Generate official transcript for a student"""
    student = get_object_or_404(User, id=student_id, role='student')
    
    # Get all completed enrollments with final_grade OR available numeric score
    try:
        enrollments = Enrollment.objects.filter(
            student=student,
        ).select_related('subject').order_by('academic_year', 'semester')
    except OperationalError as e:
        # Likely DB migrations not applied for related apps
        messages.error(request, (
            "Database error while loading enrollments. "
            "If you see 'no such table: ranks_grade' or similar, run: \n"
            "    python manage.py migrate ranks\n"
            "then restart the server."))
        return redirect('manage_academic_records')
    
    # Group by academic year and semester and collect numeric scores where available
    transcripts_by_year = {}
    detailed_rows = []
    for enrollment in enrollments:
        key = f"{enrollment.academic_year} - {enrollment.get_semester_display()}"
        if key not in transcripts_by_year:
            transcripts_by_year[key] = []

        # Try to get numeric score from ranks.Grade if available
        numeric_score = None
        subject_rank = None
        try:
            if RankGrade is not None:
                rg = RankGrade.objects.filter(student=student, subject=enrollment.subject).first()
                if rg and rg.score is not None:
                    numeric_score = rg.score
                    # compute subject rank
                    subject_rankings = rank_students_for_subject(enrollment.subject)
                    for s, sc, r in subject_rankings:
                        if s.id == student.id:
                            subject_rank = r
                            break
        except OperationalError:
            messages.error(request, "Database schema for ranks not found. Run `python manage.py migrate ranks`.")
            return redirect('manage_academic_records')

        # If numeric score not available, check enrollment.result field
        if numeric_score is None:
            result_val = getattr(enrollment, 'result', None)
            if result_val:
                try:
                    numeric_score = float(result_val)
                except (ValueError, TypeError):
                    pass

        # If still not available, try to derive from enrollment.final_grade (for backward compatibility)
        if numeric_score is None:
            numeric_score = letter_grade_to_numeric(getattr(enrollment, 'final_grade', None))
        
        letter_grade = enrollment.final_grade
        transcripts_by_year[key].append({
            'subject': enrollment.subject,
            'letter_grade': letter_grade,
            'numeric_score': numeric_score,
            'subject_rank': subject_rank,
        })
        detailed_rows.append((enrollment, numeric_score))
    
    # Calculate cumulative GPA
    total_credits = 0
    total_grade_points = 0
    
    # Compute cumulative GPA using available letter grades or mapping from numeric score
    for enrollment, numeric_score in detailed_rows:
        credits = getattr(enrollment.subject, 'credit_hours', 0) or 0
        if numeric_score is not None:
            # map numeric to grade point
            if numeric_score >= 90:
                gp = 4.0
            elif numeric_score >= 80:
                gp = 3.0
            elif numeric_score >= 70:
                gp = 2.0
            elif numeric_score >= 60:
                gp = 1.0
            else:
                gp = 0.0
        elif enrollment.final_grade:
            gp = {
                'A': 4.0, 'B': 3.0, 'C': 2.0, 'D': 1.0, 'F': 0.0
            }.get(enrollment.final_grade.upper(), 0.0)
        else:
            continue

        total_grade_points += gp * credits
        total_credits += credits
    
    cumulative_gpa = total_grade_points / total_credits if total_credits > 0 else 0
    
    # Compute numeric average (out of 100) using ranks.calculate_student_average if available
    numeric_average = None
    total_result = 0.0
    graded_count = 0
    try:
        if RankGrade is not None:
            numeric_average = calculate_student_average(student)
            # Calculate total result from all numeric scores
            for enrollment, numeric_score in detailed_rows:
                if numeric_score is not None:
                    total_result += numeric_score
                    graded_count += 1
        else:
            # Fallback: calculate from enrollments directly
            for enrollment, numeric_score in detailed_rows:
                if numeric_score is not None:
                    total_result += numeric_score
                    graded_count += 1
            if graded_count > 0:
                numeric_average = total_result / graded_count
    except OperationalError:
        # missing ranks table
        numeric_average = None
        # Calculate from enrollments directly
        for enrollment, numeric_score in detailed_rows:
            if numeric_score is not None:
                total_result += numeric_score
                graded_count += 1
        if graded_count > 0:
            numeric_average = total_result / graded_count

    # Compute student's rank among peers in same grade (by numeric average)
    student_rank = None
    try:
        if RankGrade is not None:
            peers = User.objects.filter(role='student', studentprofile__grade_level=student.studentprofile.grade_level)
            peer_averages = []
            for p in peers:
                avg = calculate_student_average(p) or 0
                peer_averages.append((p.id, avg))
            peer_averages.sort(key=lambda x: x[1], reverse=True)
            rank = 0
            last_score = None
            idx = 0
            for pid, avg in peer_averages:
                idx += 1
                if avg == last_score:
                    # same rank
                    pass
                else:
                    rank = idx
                    last_score = avg
                if pid == student.id:
                    student_rank = rank
                    break
    except OperationalError:
        student_rank = None

    context = {
        'student': student,
        'transcripts_by_year': transcripts_by_year,
        'total_credits': total_credits,
        'cumulative_gpa': round(cumulative_gpa, 2),
        'numeric_average': round(numeric_average, 2) if numeric_average is not None else None,
        'total_result': round(total_result, 2) if total_result > 0 else None,
        'student_rank': student_rank,
    }
    
    return render(request, 'registrar/official_transcript.html', context)


@login_required
@user_passes_test(is_registrar)
def enter_numeric_score(request, student_id, subject_id):
    """Registrar can enter or update numeric score (out of 100) for a student's subject.

    Creates or updates `ranks.Grade` entry.
    """
    student = get_object_or_404(User, id=student_id, role='student')
    subject = get_object_or_404(Subject, id=subject_id)

    if RankGrade is None:
        messages.error(request, 'Grades table not available. Run `python manage.py migrate ranks` and try again.')
        return redirect('student_academic_record', student_id=student_id)

    if request.method == 'POST':
        try:
            score = request.POST.get('score')
            remarks = request.POST.get('remarks', '')
            score_val = None
            if score is not None and score != '':
                score_val = int(score)
                if score_val < 0 or score_val > 100:
                    raise ValueError('Score must be between 0 and 100')

            obj, created = RankGrade.objects.get_or_create(student=student, subject=subject)
            obj.score = score_val
            obj.remarks = remarks
            obj.save()
            messages.success(request, f'Numeric score updated for {student.get_full_name()} - {subject.code}')
        except ValueError as ve:
            messages.error(request, f'Invalid score: {ve}')
        except Exception as e:
            messages.error(request, f'Error saving numeric score: {e}')

    return redirect('student_academic_record', student_id=student_id)