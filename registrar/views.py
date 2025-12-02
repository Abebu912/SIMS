from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from users.decorators import registrar_required
from users.models import User, StudentProfile
from subjects.models import Subject, Enrollment
from ranks.models import Grade, calculate_student_average
from teachers.views import enroll_students_for_subject
from django.db.utils import OperationalError
from notifications.models import Notification
from django.core.mail import send_mail
from django.conf import settings
import csv
import io
# ReportLab is an optional dependency used to generate PDF transcripts.
# Import it lazily; if it's missing, set a flag so the rest of the app
# (and migrations) can continue to run without ReportLab installed.
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except Exception:
    REPORTLAB_AVAILABLE = False

@registrar_required
def registrar_dashboard(request):
    pending_enrollments = Enrollment.objects.filter(status='pending').count()
    total_students = User.objects.filter(role='student', is_approved=True).count()
    total_subjects = Subject.objects.filter(is_active=True).count()
    
    # Get unread notifications for the registrar
    from notifications.models import Notification
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')[:5]
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    
    context = {
        'pending_enrollments': pending_enrollments,
        'total_students': total_students,
        'total_subjects': total_subjects,
        'unread_notifications': unread_notifications,
        'unread_count': unread_count,
    }
    return render(request, 'registrar/registrar_dashboard.html', context)

@registrar_required
def approve_registrations(request):
    pending_enrollments = list(Enrollment.objects.filter(status='pending').select_related('student', 'subject'))
    waitlisted_enrollments = list(Enrollment.objects.filter(status='waitlisted').select_related('student', 'subject'))

    # Precompute current enrollment counts for template use (templates can't call methods with args)
    for enrollment in pending_enrollments + waitlisted_enrollments:
        try:
            enrollment.current_count = enrollment.subject.current_enrollment_count(enrollment.academic_year, enrollment.semester)
        except Exception:
            enrollment.current_count = 0
    
    if request.method == 'POST':
        enrollment_id = request.POST.get('enrollment_id')
        action = request.POST.get('action')
        enrollment = get_object_or_404(Enrollment, id=enrollment_id)
        
        if action == 'approve':
            # Check if subject has capacity
            subject = enrollment.subject
            current_count = subject.current_enrollment_count(enrollment.academic_year, enrollment.semester)
            if current_count < subject.max_capacity:
                enrollment.status = 'approved'
                messages.success(request, f'Enrollment approved for {enrollment.student.username}.')
            else:
                enrollment.status = 'waitlisted'
                messages.warning(request, 'Subject is full. Student added to waitlist.')
        elif action == 'reject':
            enrollment.status = 'rejected'
            messages.success(request, f'Enrollment rejected for {enrollment.student.username}.')
        elif action == 'approve_waitlist':
            # Manually approve waitlisted student
            enrollment.status = 'approved'
            # nothing to add to course/student lists here; enrollment.save will persist the status
            messages.success(request, f'Waitlisted enrollment approved for {enrollment.student.username}.')
        
        enrollment.save()
        return redirect('approve_registrations')
    
    context = {
        'pending_enrollments': pending_enrollments,
        'waitlisted_enrollments': waitlisted_enrollments,
    }
    return render(request, 'registrar/approve_registrations.html', context)

@registrar_required
def manage_academic_records(request):
    students = User.objects.filter(role='student', is_approved=True).select_related('studentprofile')
    selected_student_id = request.GET.get('student_id')
    
    if selected_student_id:
        student = get_object_or_404(User, id=selected_student_id, role='student')
        enrollments = Enrollment.objects.filter(student=student).select_related('subject')
        try:
            grades = Grade.objects.filter(student=student).select_related('subject')
        except OperationalError:
            from django.contrib import messages
            messages.error(request, 'Database tables for the `ranks` app are missing. Please run `python manage.py migrate`.')
            grades = []
    else:
        student = None
        enrollments = []
        grades = []
    
    context = {
        'students': students,
        'selected_student': student,
        'enrollments': enrollments,
        'grades': grades,
    }
    return render(request, 'registrar/academic_records.html', context)

@registrar_required
def handle_waitlist(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    waitlisted_enrollments = Enrollment.objects.filter(subject=subject, status='waitlisted')
    
    if request.method == 'POST':
        enrollment_id = request.POST.get('enrollment_id')
        action = request.POST.get('action')
        
        if action == 'approve':
            enrollment = get_object_or_404(Enrollment, id=enrollment_id)
            current_count = subject.current_enrollment_count(enrollment.academic_year, enrollment.semester)
            if current_count < subject.max_capacity:
                enrollment.status = 'approved'
                enrollment.save()
                messages.success(request, 'Student approved from waitlist.')
            else:
                messages.error(request, 'Subject is at full capacity.')
        
        return redirect('handle_waitlist', subject_id=subject_id)
    
    context = {
        'subject': subject,
        'waitlisted_enrollments': waitlisted_enrollments,
    }
    return render(request, 'registrar/handle_waitlist.html', context)

@registrar_required
def generate_transcripts(request):
    # Get filter parameters
    grade_level = request.GET.get('grade_level', '')
    academic_year = request.GET.get('academic_year', '')
    semester = request.GET.get('semester', '')
    selected_student_id = request.GET.get('student_id')
    
    # Get unique values for filters
    grade_levels = StudentProfile.objects.values_list('grade_level', flat=True).distinct().order_by('grade_level')
    academic_years = Enrollment.objects.values_list('academic_year', flat=True).distinct().order_by('-academic_year')
    
    # Filter students based on criteria
    students_qs = User.objects.filter(role='student', is_approved=True).select_related('studentprofile')
    
    if grade_level:
        students_qs = students_qs.filter(studentprofile__grade_level=grade_level)
    
    if academic_year:
        students_qs = students_qs.filter(subject_enrollments__academic_year=academic_year).distinct()
    
    if semester:
        students_qs = students_qs.filter(subject_enrollments__semester=semester).distinct()
    
    students = students_qs.order_by('username')
    
    student = None
    grades = []
    total_result = None
    numeric_average = None
    student_rank = None
    
    if selected_student_id:
        student = get_object_or_404(User, id=selected_student_id, role='student')
        try:
            grades = Grade.objects.filter(student=student).select_related('subject')
            
            # Calculate total result and average
            total_result = 0.0
            graded_count = 0
            for grade in grades:
                if grade.score is not None:
                    total_result += grade.score
                    graded_count += 1
            
            if graded_count > 0:
                numeric_average = total_result / graded_count
            else:
                numeric_average = None
            
            # Calculate student rank among peers in same grade level
            try:
                if hasattr(student, 'studentprofile') and student.studentprofile.grade_level:
                    peers = User.objects.filter(
                        role='student', 
                        is_approved=True,
                        studentprofile__grade_level=student.studentprofile.grade_level
                    )
                    peer_averages = []
                    for peer in peers:
                        try:
                            avg = calculate_student_average(peer) or 0
                            peer_averages.append((peer.id, avg))
                        except Exception:
                            pass
                    
                    peer_averages.sort(key=lambda x: x[1], reverse=True)
                    rank = 0
                    last_score = None
                    idx = 0
                    for pid, avg in peer_averages:
                        idx += 1
                        if avg == last_score:
                            pass  # same rank
                        else:
                            rank = idx
                            last_score = avg
                        if pid == student.id:
                            student_rank = rank
                            break
            except Exception:
                student_rank = None
                
        except OperationalError:
            from django.contrib import messages
            messages.error(request, 'Database tables for the `ranks` app are missing. Please run `python manage.py migrate`.')
            grades = []
        
        if request.GET.get('format') == 'pdf':
            return generate_pdf_transcript(student, grades)
        elif request.GET.get('format') == 'csv':
            return generate_csv_transcript(student, grades)
    
    context = {
        'students': students,
        'selected_student': student,
        'grades': grades,
        'total_result': round(total_result, 2) if total_result is not None else None,
        'numeric_average': round(numeric_average, 2) if numeric_average is not None else None,
        'student_rank': student_rank,
        'grade_levels': grade_levels,
        'academic_years': academic_years,
        'current_filters': {
            'grade_level': grade_level,
            'academic_year': academic_year,
            'semester': semester,
        },
    }
    return render(request, 'registrar/generate_transcripts.html', context)


@registrar_required
def assign_subjects_to_teacher(request):
    """Registrar view: assign subjects to a teacher.

    GET: show form with teachers and available subjects (filter by grade/term)
    POST: assign selected subject ids or assign all unassigned subjects for a grade/term to the teacher
    """
    from subjects.models import Subject, Teacher as TeacherModel

    teachers = User.objects.filter(role='teacher').order_by('username')

    # Filters
    grade_level = request.GET.get('grade_level')
    academic_year = request.GET.get('academic_year')
    semester = request.GET.get('semester')

    # Clean up any subjects that were self-assigned by teachers (not assigned by registrar)
    # We will unset the instructor for those subjects so only registrar-assigned subjects remain.
    try:
        self_assigned = Subject.objects.filter(instructor__isnull=False, assigned_by_registrar=False)
        for s in self_assigned:
            s.instructor = None
            s.save()
    except Exception:
        pass

    available_qs = Subject.objects.filter(instructor__isnull=True, is_active=True)
    if grade_level:
        try:
            available_qs = available_qs.filter(grade_level=int(grade_level))
        except Exception:
            pass

    available_subjects = available_qs.order_by('grade_level', 'code')

    # Also provide currently assigned subjects (so registrar can unassign individual ones)
    assigned_qs = Subject.objects.filter(instructor__isnull=False, is_active=True)
    if grade_level:
        try:
            assigned_qs = assigned_qs.filter(grade_level=int(grade_level))
        except Exception:
            pass
    assigned_subjects = assigned_qs.order_by('grade_level', 'code')

    if request.method == 'POST':
        teacher_user_id = request.POST.get('teacher_user_id')
        subject_ids = request.POST.getlist('subject_ids')
        assign_all = request.POST.get('assign_all') == '1'

        if not teacher_user_id:
            messages.error(request, 'Please select a teacher to assign to.')
            return redirect('assign_subjects_to_teacher')

        try:
            teacher_user = User.objects.get(id=int(teacher_user_id), role='teacher')
            teacher_obj, created = TeacherModel.objects.get_or_create(user=teacher_user, defaults={'teacher_id': f'T{teacher_user.id}', 'department': ''})
        except Exception:
            messages.error(request, 'Teacher not found.')
            return redirect('assign_subjects_to_teacher')

        assigned = 0
        if assign_all:
            subjects_to_assign = available_qs
        else:
            subjects_to_assign = Subject.objects.filter(id__in=subject_ids, instructor__isnull=True)

        # Require academic_year and semester for assignment
        post_academic_year = request.POST.get('academic_year')
        post_semester = request.POST.get('semester')
        if not post_academic_year or not post_semester:
            messages.error(request, 'Academic year and semester are required to assign subjects.')
            return redirect('assign_subjects_to_teacher')

        for subj in subjects_to_assign:
            subj.instructor = teacher_obj
            subj.assigned_by_registrar = True
            subj.save()
            try:
                # auto-enroll students for provided academic_year/semester
                enroll_students_for_subject(subj, academic_year=post_academic_year, semester=post_semester, status='approved')
            except Exception:
                pass

            # create a notification for the teacher
            try:
                Notification.objects.create(
                    user=teacher_user,
                    title='Subject Assignment',
                    message=f'You have been assigned to teach {subj.code} - {subj.name} for {post_academic_year} ({post_semester}).',
                    link=f'/teachers/enter-grades/?subject_id={subj.id}'
                )
            except Exception:
                pass

            # send an email to the teacher (best-effort)
            try:
                if teacher_user.email:
                    send_mail(
                        subject=f'Subject assigned: {subj.code}',
                        message=f'Hello {teacher_user.get_full_name() or teacher_user.username},\n\nYou have been assigned to teach {subj.name} ({subj.code}) for {post_academic_year} - {post_semester}.\n\nPlease login to the system to view your classes and enter results.\n',
                        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
                        recipient_list=[teacher_user.email],
                        fail_silently=True,
                    )
            except Exception:
                pass

            assigned += 1

        # Prepare success message
        success_msg = f'Successfully assigned {assigned} subject(s) to {teacher_user.get_full_name() or teacher_user.username}.'

        # If AJAX request, return JSON so frontend can update without full reload
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'assigned': assigned, 'message': success_msg})

        messages.success(request, success_msg)
        # Redirect back to the assign page (preserve filters) so the message is shown on the same view
        params = []
        if grade_level:
            params.append(f'grade_level={grade_level}')
        if post_academic_year:
            params.append(f'academic_year={post_academic_year}')
        if post_semester:
            params.append(f'semester={post_semester}')
        query = ('?' + '&'.join(params)) if params else ''
        return redirect('assign_subjects_to_teacher' + query)

    context = {
        'teachers': teachers,
        'available_subjects': available_subjects,
        'assigned_subjects': assigned_subjects,
        'filter_grade_level': grade_level,
        'filter_academic_year': academic_year,
        'filter_semester': semester,
    }
    return render(request, 'registrar/assign_subjects.html', context)


@registrar_required
def unassign_subject_from_teacher(request, subject_id=None):
    """Registrar: unassign a subject from its current teacher or bulk-unassign by teacher id.

    POST parameters:
    - subject_id (url param): unassign this subject
    - or teacher_user_id (form): unassign all subjects currently assigned to this teacher
    """
    from subjects.models import Subject, Teacher as TeacherModel

    # Unassign single subject via URL
    if request.method == 'POST' and subject_id:
        subj = get_object_or_404(Subject, id=subject_id)
        prev_instructor = subj.instructor
        subj.instructor = None
        subj.assigned_by_registrar = False
        subj.save()

        # notify previous teacher if possible
        try:
            if prev_instructor and prev_instructor.user and prev_instructor.user.email:
                Notification.objects.create(
                    user=prev_instructor.user,
                    title='Subject Unassigned',
                    message=f'You have been unassigned from {subj.code} - {subj.name}.',
                )
        except Exception:
            pass

        # Return JSON for AJAX callers
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'subject_id': subject_id, 'code': subj.code, 'name': subj.name})

        messages.success(request, f'Unassigned {subj.code} - {subj.name} from its teacher.')
        return redirect('assign_subjects_to_teacher')

    # Bulk unassign by teacher (form post)
    if request.method == 'POST':
        teacher_user_id = request.POST.get('teacher_user_id')
        if not teacher_user_id:
            messages.error(request, 'Please select a teacher to unassign.')
            return redirect('assign_subjects_to_teacher')

        try:
            teacher_user = User.objects.get(id=int(teacher_user_id), role='teacher')
            teacher_obj = TeacherModel.objects.filter(user=teacher_user).first()
        except Exception:
            messages.error(request, 'Teacher not found.')
            return redirect('assign_subjects_to_teacher')

        if not teacher_obj:
            messages.info(request, 'Teacher has no assigned subjects.')
            return redirect('assign_subjects_to_teacher')

        subjects_qs = Subject.objects.filter(instructor=teacher_obj)
        count = subjects_qs.update(instructor=None, assigned_by_registrar=False)
        messages.success(request, f'Unassigned {count} subject(s) from {teacher_user.get_full_name()}.')
        return redirect('assign_subjects_to_teacher')

    # If GET, redirect to assign page
    return redirect('assign_subjects_to_teacher')

def generate_csv_transcript(student, grades):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{student.username}_transcript.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Student ID', 'Name', 'Course', 'Result (out of 100)'])
    
    total_result = 0.0
    graded_count = 0
    
    for grade in grades:
        score = grade.score if grade.score is not None else None
        if score is not None:
            total_result += score
            graded_count += 1
        
        writer.writerow([
            student.studentprofile.student_id,
            student.get_full_name(),
            grade.subject.name,
            int(score) if score is not None else 'N/A'
        ])
    
    # Add summary rows
    writer.writerow([])  # Empty row
    writer.writerow(['Total Result', int(total_result) if total_result > 0 else 'N/A'])
    numeric_average = total_result / graded_count if graded_count > 0 else None
    writer.writerow(['Average Result', f"{numeric_average:.1f} / 100" if numeric_average else 'N/A'])
    
    # Calculate student rank
    student_rank = None
    try:
        if hasattr(student, 'studentprofile') and student.studentprofile.grade_level:
            peers = User.objects.filter(
                role='student', 
                is_approved=True,
                studentprofile__grade_level=student.studentprofile.grade_level
            )
            peer_averages = []
            for peer in peers:
                try:
                    avg = calculate_student_average(peer) or 0
                    peer_averages.append((peer.id, avg))
                except Exception:
                    pass
            
            peer_averages.sort(key=lambda x: x[1], reverse=True)
            rank = 0
            last_score = None
            idx = 0
            for pid, avg in peer_averages:
                idx += 1
                if avg == last_score:
                    pass
                else:
                    rank = idx
                    last_score = avg
                if pid == student.id:
                    student_rank = rank
                    break
    except Exception:
        pass
    
    writer.writerow(['Class Rank', f"#{student_rank}" if student_rank else 'N/A'])
    
    return response

def generate_pdf_transcript(student, grades):
    """Generate PDF transcript using ReportLab"""
    if not REPORTLAB_AVAILABLE:
        return HttpResponse("PDF generation requires ReportLab. Install with `pip install reportlab`.", status=503)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        alignment=1,  # Center alignment
        spaceAfter=30
    )
    story.append(Paragraph("ACADEMIC TRANSCRIPT", title_style))
    
    # Student Information
    student_info = f"""
    <b>Student Name:</b> {student.get_full_name() or student.username}<br/>
    <b>Student ID:</b> {getattr(student.studentprofile, 'student_id', 'N/A')}<br/>
    <b>Grade Level:</b> Grade {getattr(student.studentprofile, 'grade_level', 'N/A')}<br/>
    <b>Generated Date:</b> {timezone.now().strftime('%Y-%m-%d')}
    """
    story.append(Paragraph(student_info, styles["Normal"]))
    story.append(Spacer(1, 20))
    
    # Grades Table
    if grades:
        data = [['Course', 'Result (out of 100)']]
        total_result = 0.0
        graded_count = 0
        
        for grade in grades:
            score = grade.score if grade.score is not None else None
            if score is not None:
                total_result += score
                graded_count += 1
            
            data.append([
                grade.subject.name,
                str(int(score)) if score is not None else 'N/A'
            ])
        
        # Create table
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(table)
        story.append(Spacer(1, 20))
        
        # Calculate average
        numeric_average = total_result / graded_count if graded_count > 0 else None
        
        # Calculate student rank
        student_rank = None
        try:
            if hasattr(student, 'studentprofile') and student.studentprofile.grade_level:
                peers = User.objects.filter(
                    role='student', 
                    is_approved=True,
                    studentprofile__grade_level=student.studentprofile.grade_level
                )
                peer_averages = []
                for peer in peers:
                    try:
                        avg = calculate_student_average(peer) or 0
                        peer_averages.append((peer.id, avg))
                    except Exception:
                        pass
                
                peer_averages.sort(key=lambda x: x[1], reverse=True)
                rank = 0
                last_score = None
                idx = 0
                for pid, avg in peer_averages:
                    idx += 1
                    if avg == last_score:
                        pass
                    else:
                        rank = idx
                        last_score = avg
                    if pid == student.id:
                        student_rank = rank
                        break
        except Exception:
            pass
        
        # Summary Section
        summary_data = [
            ['Total Result', str(int(total_result)) if total_result > 0 else 'N/A'],
            ['Average Result', f"{numeric_average:.1f} / 100" if numeric_average else 'N/A'],
            ['Class Rank', f"#{student_rank}" if student_rank else 'N/A']
        ]
        
        summary_table = Table(summary_data)
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey, colors.white])
        ]))
        story.append(summary_table)
    else:
        story.append(Paragraph("No grades available.", styles["Normal"]))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{student.username}_transcript.pdf"'
    return response

def get_grade_point(grade):
    """Convert letter grade to grade point"""
    if not grade:
        return 0.0
        
    grade_points = {
        'A': 4.0, 'A-': 3.7,
        'B+': 3.3, 'B': 3.0, 'B-': 2.7,
        'C+': 2.3, 'C': 2.0, 'C-': 1.7,
        'D+': 1.3, 'D': 1.0, 'D-': 0.7,
        'F': 0.0
    }
    return grade_points.get(grade.upper(), 0.0)