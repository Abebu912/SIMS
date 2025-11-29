from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django import forms
from django.core.mail import send_mail
from django.conf import settings
from students.models import Student
from users.decorators import parent_required
from users.models import User, StudentParent
from subjects.models import Subject, Enrollment
from ranks.models import Grade
from django.db.utils import OperationalError
from payments.models import Payment
from notifications.models import Announcement
from django.utils import timezone
from .models import ChildLinkRequest


# Simple form class for requesting a child link
class ChildLinkRequestForm(forms.ModelForm):
    class Meta:
        model = ChildLinkRequest
        fields = [
            'child_identifier',
            'relationship',
            'message',
        ]

    def clean_child_identifier(self):
        identifier = self.cleaned_data.get('child_identifier', '').strip()
        if not identifier:
            raise forms.ValidationError('Please provide a student identifier (ID, email or username).')

        student = None
        student_user = None

        # Try to match using Student model first
        student = Student.objects.filter(student_id__iexact=identifier).first()
        if not student:
            student = Student.objects.filter(user__email__iexact=identifier).first()
        if not student:
            student = Student.objects.filter(user__username__iexact=identifier).first()
        
        # If not found in Student model, try User with studentprofile
        if not student:
            from users.models import User, StudentProfile
            # Try by studentprofile.student_id
            try:
                student_profile = StudentProfile.objects.filter(student_id__iexact=identifier).first()
                if student_profile:
                    student_user = student_profile.user
            except:
                pass
            
            # Try by email
            if not student_user:
                student_user = User.objects.filter(role='student', email__iexact=identifier).first()
            
            # Try by username
            if not student_user:
                student_user = User.objects.filter(role='student', username__iexact=identifier).first()
            
            # If identifier looks like an email and we didn't find an exact match, try fuzzy search
            if not student_user and '@' in identifier:
                normalized = identifier.strip().lower()
                candidates = User.objects.filter(role='student', email__icontains=normalized)
                count = candidates.count()
                if count == 1:
                    student_user = candidates.first()
                elif count > 1:
                    examples = []
                    for c in candidates[:5]:
                        name = c.get_full_name() or c.username
                        try:
                            sid = c.studentprofile.student_id if hasattr(c, 'studentprofile') else 'N/A'
                        except:
                            sid = 'N/A'
                        examples.append(f"{name} ({sid})")
                    more = '...' if count > 5 else ''
                    raise forms.ValidationError(
                        'Multiple students match that email. Please enter the student ID to be specific. ' \
                        f'Possible matches: {", ".join(examples)}{more}'
                    )
        
        # If we found a student_user but not a Student model, create a wrapper
        if student_user and not student:
            # Create a pseudo-student object for compatibility
            class PseudoStudent:
                def __init__(self, user):
                    self.user = user
                    try:
                        self.student_id = user.studentprofile.student_id
                    except:
                        self.student_id = f"STU{user.id:06d}"
            
            student = PseudoStudent(student_user)
            self._matched_student_user = student_user
        elif student:
            self._matched_student_user = student.user

        if not student:
            raise forms.ValidationError('No student found matching that identifier. Please check and try again (try student ID, email, or username).')

        # store matched_student on the form for use in the view
        self._matched_student = student
        return identifier


class MessageTeacherForm(forms.Form):
    subject = forms.CharField(max_length=255)
    message = forms.CharField(widget=forms.Textarea)


@parent_required
def message_teacher(request, teacher_id):
    """Send a simple email to a teacher (by user id)."""
    teacher = get_object_or_404(User, id=teacher_id, role='teacher')
    if request.method == 'POST':
        form = MessageTeacherForm(request.POST)
        if form.is_valid():
            subject = form.cleaned_data['subject']
            message_body = form.cleaned_data['message']
            recipient = teacher.email
            if recipient:
                try:
                    send_mail(subject, message_body, settings.DEFAULT_FROM_EMAIL, [recipient], fail_silently=False)
                    messages.success(request, 'Message sent to the teacher.')
                except Exception:
                    messages.error(request, 'Failed to send message. Please try later.')
            else:
                messages.error(request, 'Teacher has no email address on record.')
            # Redirect back to contact teachers list for the student if provided, else to the parent contact overview
            student_id = request.GET.get('student_id')
            if student_id:
                return redirect('contact_teachers', student_id=student_id)
            return redirect('parent_contact_teachers_overview')
    else:
        form = MessageTeacherForm(initial={'subject': f'Message from parent {request.user.get_full_name()}'})

    context = {'form': form, 'teacher': teacher}
    return render(request, 'parents/message_teacher.html', context)

@parent_required
def parent_dashboard(request):
    """Parent dashboard showing their children's overview"""
    # Get all children linked to this parent
    children = StudentParent.objects.filter(parent=request.user).select_related('student')
    
    children_data = []
    for child_link in children:
        child = child_link.student
        # Get child's recent grades
        try:
            recent_grades = Grade.objects.filter(student=child).select_related('subject')[:5]
        except OperationalError:
            recent_grades = []
        # Get child's current courses
        current_courses = Enrollment.objects.filter(
            student=child, 
            status='approved'
        ).select_related('subject')
        # Get pending fees
        pending_fees = Payment.objects.filter(student=child, status='pending')
        
        children_data.append({
            'student': child,
            'relationship': child_link.relationship,
            'recent_grades': recent_grades,
            'current_courses': current_courses.count(),
            'pending_fees': pending_fees.count(),
        })
    
    # Get unread notifications for the parent
    from notifications.models import Notification
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')[:5]
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    
    context = {
        'children_data': children_data,
        'total_children': children.count(),
        'unread_notifications': unread_notifications,
        'unread_count': unread_count,
    }
    return render(request, 'parents/parent_dashboard.html', context)

@parent_required
def view_children(request):
    """View all children linked to parent"""
    children_links = StudentParent.objects.filter(parent=request.user).select_related('student')
    
    context = {
        'children_links': children_links,
    }
    return render(request, 'parents/view_children.html', context)

@parent_required
def child_grades(request, student_id):
    """View specific child's grades"""
    # Verify the student is actually this parent's child
    child_link = get_object_or_404(StudentParent, parent=request.user, student_id=student_id)
    child = child_link.student
    
    try:
        grades = Grade.objects.filter(student=child).select_related('subject').order_by('subject__code')
    except OperationalError:
        from django.contrib import messages
        messages.error(request, 'Database tables for the `ranks` app are missing. Please run `python manage.py migrate`.')
        grades = []
    
    # Calculate GPA for this child
    total_credits = 0
    total_points = 0
    for grade in grades:
        if grade.grade and grade.credits:
            grade_point = get_grade_point(grade.grade)
            total_credits += grade.credits
            total_points += grade_point * grade.credits
    
    gpa = total_points / total_credits if total_credits > 0 else 0
    
    context = {
        'child': child,
        'relationship': child_link.relationship,
        'grades': grades,
        'gpa': round(gpa, 2),
        'total_credits': total_credits,
    }
    return render(request, 'parents/child_grades.html', context)

@parent_required
def child_ranks(request, student_id):
    """View child's attendance (placeholder - integrate with attendance app later)"""
    child_link = get_object_or_404(StudentParent, parent=request.user, student_id=student_id)
    child = child_link.student
    
    
    try:
        grades_qs = Grade.objects.filter(student=child).select_related('subject').order_by('subject__code')
    except OperationalError:
        from django.contrib import messages
        messages.error(request, 'Database tables for the `ranks` app are missing. Please run `python manage.py migrate`.')
        grades_qs = []

    # Build subject results list (numeric scores)
    subject_results = []
    for g in grades_qs:
        subject_results.append({'subject': g.subject, 'score': g.score})

    # Compute weighted average (numeric) using ranks.calculate_student_average
    from ranks.models import calculate_student_average, rank_students_for_subject
    avg = calculate_student_average(child)

    # Compute class rank among students in same grade (if available)
    class_rank = None
    try:
        if hasattr(child, 'studentprofile') and child.studentprofile.grade_level:
            grade_level = child.studentprofile.grade_level
            peers = User.objects.filter(role='student', studentprofile__grade_level=grade_level)
            peer_averages = []
            for peer in peers:
                peer_avg = calculate_student_average(peer)
                if peer_avg is not None:
                    peer_averages.append((peer.id, peer_avg))
            # sort descending
            peer_averages.sort(key=lambda x: x[1], reverse=True)
            for idx, (peer_id, pa) in enumerate(peer_averages, start=1):
                if peer_id == child.id:
                    class_rank = idx
                    break
    except Exception:
        class_rank = None

    context = {
        'child': child,
        'relationship': child_link.relationship,
        'subject_results': subject_results,
        'average': round(avg, 2) if avg is not None else None,
        'class_rank': class_rank,
    }
    return render(request, 'parents/child_ranks.html', context)
    
@parent_required
def child_schedule(request, student_id):
    """View specific child's schedule"""
    child_link = get_object_or_404(StudentParent, parent=request.user, student_id=student_id)
    child = child_link.student

    # Get enrolled courses
    enrollments = Enrollment.objects.filter(
        student=child,
        status='approved'
    ).select_related('subject__instructor__user')

    # Placeholder schedule - integrate with your scheduling system
    schedule_data = [
        {'day': 'Monday', 'time': '09:00-10:30', 'course': 'Mathematics', 'room': 'Room 101'},
        {'day': 'Monday', 'time': '11:00-12:30', 'course': 'Science', 'room': 'Lab A'},
        {'day': 'Tuesday', 'time': '09:00-10:30', 'course': 'English', 'room': 'Room 102'},
        {'day': 'Wednesday', 'time': '14:00-15:30', 'course': 'History', 'room': 'Room 103'},
    ]

    context = {
        'child': child,
        'relationship': child_link.relationship,
        'enrollments': enrollments,
        'schedule_data': schedule_data,
    }
    return render(request, 'parents/child_schedule.html', context)

@parent_required
def child_fees(request, student_id):
    """View and pay child's fees"""
    child_link = get_object_or_404(StudentParent, parent=request.user, student_id=student_id)
    child = child_link.student
    
    payments = Payment.objects.filter(student=child).select_related('fee_structure').order_by('-payment_date')
    
    if request.method == 'POST':
        fee_structure_id = request.POST.get('fee_structure_id')
        # In a real system, you would integrate with a payment gateway
        messages.success(request, f'Payment initiated for {child.get_full_name()}.')
        return redirect('child_fees', student_id=student_id)
    
    context = {
        'child': child,
        'relationship': child_link.relationship,
        'payments': payments,
        'pending_payments': payments.filter(status='pending'),
        'completed_payments': payments.filter(status='completed'),
    }
    return render(request, 'parents/child_fees.html', context)

@parent_required
def school_announcements(request):
    """View school announcements relevant to parents"""
    # FIXED: Replace contains lookup with database-agnostic approach
    try:
        # Get all active announcements first
        all_announcements = Announcement.objects.filter(is_active=True).order_by('-created_at')
        
        # Filter in Python instead of using contains lookup
        relevant_announcements = []
        for announcement in all_announcements:
            target_roles = getattr(announcement, 'target_roles', [])
            
            # Handle different data types for target_roles
            if isinstance(target_roles, str):
                # If it's stored as a string, try to parse it
                try:
                    import json
                    target_roles = json.loads(target_roles)
                except:
                    # If parsing fails, treat as comma-separated
                    target_roles = [role.strip() for role in target_roles.split(',') if role.strip()]
            elif not isinstance(target_roles, list):
                target_roles = []
            
            # Check if announcement targets parents or is for everyone
            # Empty list or no target_roles means show to all
            if not target_roles or len(target_roles) == 0 or 'parent' in target_roles:
                relevant_announcements.append(announcement)
                
    except Exception as e:
        # Fallback: get all active announcements if there's an error
        relevant_announcements = Announcement.objects.filter(is_active=True).order_by('-created_at')
        print(f"Error filtering announcements: {e}")
    
    context = {
        'announcements': relevant_announcements,
    }
    return render(request, 'parents/school_announcements.html', context)

@parent_required
def contact_teachers(request, student_id):
    """View teachers for a child and contact information"""
    child_link = get_object_or_404(StudentParent, parent=request.user, student_id=student_id)
    child = child_link.student
    
    # Get teachers from child's enrolled courses
    enrollments = Enrollment.objects.filter(
        student=child, 
        status='approved'
    ).select_related('subject__instructor__user')
    
    teachers = set()
    for enrollment in enrollments:
        if getattr(enrollment, 'subject', None) and getattr(enrollment.subject, 'instructor', None):
            # instructor is Teacher model; get the linked user
            teacher_user = getattr(enrollment.subject.instructor, 'user', None)
            if teacher_user:
                teachers.add(teacher_user)
    
    context = {
        'child': child,
        'relationship': child_link.relationship,
        'teachers': list(teachers),  # Convert set to list for template
    }
    return render(request, 'parents/contact_teachers.html', context)

@parent_required
def request_meeting(request, student_id, teacher_id):
    """Request a meeting with a teacher"""
    child_link = get_object_or_404(StudentParent, parent=request.user, student_id=student_id)
    teacher = get_object_or_404(User, id=teacher_id, role='teacher')
    
    if request.method == 'POST':
        meeting_date = request.POST.get('meeting_date')
        meeting_time = request.POST.get('meeting_time')
        purpose = request.POST.get('purpose')
        
        # In a real system, you would create a meeting request in the database
        messages.success(request, f'Meeting request sent to {teacher.get_full_name()} for {meeting_date} at {meeting_time}.')
        return redirect('contact_teachers', student_id=student_id)
    
    context = {
        'child': child_link.student,
        'teacher': teacher,
        'relationship': child_link.relationship,
    }
    return render(request, 'parents/request_meeting.html', context)

@parent_required
def child_attendance(request, student_id):
    """View specific child's attendance"""
    # Verify the student is actually this parent's child
    child_link = get_object_or_404(StudentParent, parent=request.user, student_id=student_id)
    child = child_link.student

    # Placeholder attendance data - integrate with attendance app later
    attendance_data = [
        {'date': '2025-11-01', 'status': 'Present'},
        {'date': '2025-11-02', 'status': 'Absent'},
        {'date': '2025-11-03', 'status': 'Present'},
        {'date': '2025-11-04', 'status': 'Late'},
    ]

    context = {
        'child': child,
        'relationship': child_link.relationship,
        'attendance_data': attendance_data,
    }
    return render(request, 'parents/child_attendance.html', context)


@parent_required
def parent_fees_summary(request):
    """Aggregate fee statements for all children of the parent"""
    children_links = StudentParent.objects.filter(parent=request.user).select_related('student')
    summary = []
    for link in children_links:
        child = link.student
        payments = Payment.objects.filter(student=child)
        pending = payments.filter(status='pending').count()
        completed = payments.filter(status='completed').count()
        total = payments.count()
        summary.append({
            'student': child,
            'relationship': link.relationship,
            'pending': pending,
            'completed': completed,
            'total': total,
        })

    context = {
        'summary': summary,
    }
    return render(request, 'parents/parent_fees_summary.html', context)


@parent_required
def parent_progress_overview(request):
    """Show progress overview (GPA/ranks) for all children"""
    children_links = StudentParent.objects.filter(parent=request.user).select_related('student', 'student__studentprofile')
    children_progress = []
    
    for link in children_links:
        child = link.student
        try:
            # Get enrollments with results
            enrollments = Enrollment.objects.filter(student=child).select_related('subject')
            
            # Calculate scores using the same method as students
            from users.views import compute_numeric_scores
            score_map, total_result, graded_count, average_result = compute_numeric_scores(child, enrollments)
            
            # Get subject results
            subject_results = []
            for enrollment in enrollments:
                score = score_map.get(enrollment.id)
                if score is not None:
                    subject_results.append({
                        'subject': enrollment.subject.name,
                        'score': round(float(score), 2),
                        'academic_year': getattr(enrollment, 'academic_year', 'N/A'),
                        'semester': getattr(enrollment, 'get_semester_display', lambda: 'N/A')(),
                    })
            
            # Calculate class rank
            class_rank = None
            try:
                if hasattr(child, 'studentprofile') and child.studentprofile.grade_level:
                    grade_level = child.studentprofile.grade_level
                    peers = User.objects.filter(
                        role='student',
                        studentprofile__grade_level=grade_level
                    )
                    peer_data = []
                    for peer in peers:
                        peer_enrollments = Enrollment.objects.filter(student=peer)
                        _, _, _, peer_avg = compute_numeric_scores(peer, peer_enrollments)
                        if peer_avg is not None:
                            peer_data.append({
                                'student_id': peer.id,
                                'average': peer_avg
                            })
                    peer_data.sort(key=lambda x: x['average'], reverse=True)
                    for idx, peer in enumerate(peer_data, start=1):
                        if peer['student_id'] == child.id:
                            class_rank = idx
                            break
            except Exception:
                pass
            
            children_progress.append({
                'student': child,
                'relationship': link.relationship,
                'subject_results': subject_results,
                'total_result': round(total_result, 2),
                'average_result': average_result,
                'class_rank': class_rank,
                'graded_count': graded_count,
            })
        except Exception as e:
            import traceback
            traceback.print_exc()
            children_progress.append({
                'student': child,
                'relationship': link.relationship,
                'subject_results': [],
                'total_result': 0,
                'average_result': None,
                'class_rank': None,
                'graded_count': 0,
                'error': str(e)
            })
    
    context = {
        'children_progress': children_progress,
    }
    return render(request, 'parents/parent_progress.html', context)


@parent_required
def parent_contact_teachers_overview(request):
    """List teachers across all children and provide contact links"""
    children_links = StudentParent.objects.filter(parent=request.user).select_related('student')
    teacher_map = {}
    for link in children_links:
        child = link.student
        enrollments = Enrollment.objects.filter(student=child, status='approved').select_related('subject__instructor__user')
        for enrollment in enrollments:
            instructor = getattr(enrollment.subject, 'instructor', None)
            if instructor:
                user = getattr(instructor, 'user', None)
                if user:
                    teacher_map.setdefault(user.id, {'user': user, 'children': set()})
                    teacher_map[user.id]['children'].add(child)

    # Convert sets to lists for template
    teachers = []
    for t in teacher_map.values():
        teachers.append({'user': t['user'], 'children': list(t['children'])})

    context = {
        'teachers': teachers,
    }
    return render(request, 'parents/parent_contact_teachers.html', context)


@parent_required
def request_child_link(request):
    """Allow parent to request linking a child to their account."""
    if request.method == 'POST':
        form = ChildLinkRequestForm(request.POST)
        if form.is_valid():
            req = form.save(commit=False)
            req.parent = request.user
            # We validated and attached matched student on the form; include a note in message
            matched_student = getattr(form, '_matched_student', None)
            # Save request first
            req.save()

            # If we found a matching student at form validation time, automatically approve
            # by creating the StudentParent link and notifying the parent.
            if getattr(settings, 'PARENT_CHILD_LINK_AUTO_APPROVE', True) and matched_student:
                try:
                    # Get the actual user object
                    student_user = getattr(form, '_matched_student_user', None) or matched_student.user
                    
                    StudentParent.objects.get_or_create(
                        parent=req.parent,
                        student=student_user,
                        defaults={'relationship': req.relationship or 'Mother'}
                    )
                    req.status = 'approved'
                    req.save()
                    messages.success(request, f'Child "{matched_student.user.get_full_name() or matched_student.user.username}" has been successfully linked to your account!')
                    # notify the parent that the request was approved automatically
                    parent_email = req.parent.email
                    if parent_email:
                        try:
                            send_mail(
                                'Your child link request was approved',
                                f"Your request to link '{req.child_identifier}' to your account was automatically approved.",
                                settings.DEFAULT_FROM_EMAIL,
                                [parent_email],
                                fail_silently=True,
                            )
                        except Exception:
                            pass
                except Exception:
                    # If any error occurs, continue and still notify admins below
                    pass

            # notify admins (prefer Django ADMINS; fall back to staff users with emails)
            admin_emails = []
            try:
                admin_emails = [email for _name, email in settings.ADMINS if email]
            except Exception:
                admin_emails = []

            if not admin_emails:
                admin_emails = list(User.objects.filter(is_staff=True).exclude(email='').values_list('email', flat=True))

            if admin_emails:
                subject = f"Child link request from {request.user.get_full_name()}"
                body = (
                    f"Parent: {request.user.get_full_name()} ({request.user.email})\n"
                    f"Requested child identifier: {req.child_identifier}\n"
                    f"Relationship: {req.relationship}\n"
                    f"Message: {req.message or '<none>'}\n"
                    f"Submitted at: {req.created_at if getattr(req, 'created_at', None) else 'just now'}\n"
                )
                try:
                    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, admin_emails, fail_silently=True)
                except Exception:
                    pass

            messages.success(request, 'Your request has been submitted. The administration will review it.')
            return redirect('parent_dashboard')
        else:
            messages.error(request, 'Please fix the errors in the form.')
    else:
        form = ChildLinkRequestForm()

    context = {'form': form}
    return render(request, 'parents/request_child_link.html', context)

# Helper function
def get_grade_point(grade_letter):
    """Convert letter grade to grade point"""
    if not grade_letter:
        return 0.0
        
    grade_points = {
        'A': 4.0, 'A-': 3.7,
        'B+': 3.3, 'B': 3.0, 'B-': 2.7,
        'C+': 2.3, 'C': 2.0, 'C-': 1.7,
        'D+': 1.3, 'D': 1.0, 'D-': 0.7,
        'F': 0.0
    }
    return grade_points.get(grade_letter.upper(), 0.0)