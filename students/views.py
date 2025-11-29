from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
from django.http import JsonResponse
from users.decorators import student_required
from users.models import User
from subjects.models import Subject, Enrollment
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from ranks.models import Grade
from payments.models import Payment, FeeStructure
from notifications.models import Announcement
from ai_advisor.models import AIConversation, AIMessage
import json
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Student
from .serializers import StudentSerializer
from subjects.models import Subject
from subjects.serializers import SubjectSerializer

from types import SimpleNamespace
from django.conf import settings


def get_assigned_subjects_for_student(user, grade_level_override=None):
    """Return a list of pseudo-enrollment objects for core subjects matching student's grade.

    These objects mimic Enrollment with attributes used in templates: subject, status, final_grade, enrolled_date
    They are not saved to the DB; they are used to display assigned subjects when no enrollments exist yet.
    """
    if grade_level_override is not None:
        grade_level = grade_level_override
    else:
        try:
            grade_level = user.studentprofile.grade_level
        except Exception:
            try:
                grade_level = user.student_profile.grade_level
            except Exception:
                return []

    subjects = Subject.objects.filter(
        grade_level=grade_level,
        is_active=True,
        subject_type__in=getattr(settings, 'AUTO_ENROLL_SUBJECT_TYPES', ['core'])
    ).order_by('code')

    pseudo = []
    for s in subjects:
        obj = SimpleNamespace()
        obj.subject = s
        obj.status = 'assigned'
        obj.final_grade = None
        obj.enrolled_date = None
        pseudo.append(obj)
    return pseudo

@student_required
def student_dashboard(request):
    # Include approved/active/pending/waitlisted enrollments so dashboard shows current registrations
    student_enrollments = Enrollment.objects.filter(
        student=request.user,
        status__in=['approved', 'active', 'pending', 'waitlisted']
    ).select_related('subject')
    
    recent_grades = Grade.objects.filter(student=request.user).select_related('subject')[:5]
    pending_payments = Payment.objects.filter(student=request.user, status='pending')
    
    # Get unread notifications for the student
    from notifications.models import Notification
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')[:5]
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    
    # Get recent announcements for the student
    try:
        all_announcements = Announcement.objects.filter(is_active=True).order_by('-created_at')[:5]
        relevant_announcements = []
        for announcement in all_announcements:
            target_roles = getattr(announcement, 'target_roles', [])
            if isinstance(target_roles, str):
                try:
                    import json
                    target_roles = json.loads(target_roles)
                except:
                    target_roles = [role.strip() for role in target_roles.split(',') if role.strip()]
            elif not isinstance(target_roles, list):
                target_roles = []
            if not target_roles or len(target_roles) == 0 or 'student' in target_roles:
                relevant_announcements.append(announcement)
    except Exception as e:
        relevant_announcements = []
        print(f"Error loading announcements: {e}")
    
    context = {
        'enrollments': student_enrollments,
        'recent_grades': recent_grades,
        'pending_payments': pending_payments,
        'total_subjects': student_enrollments.count(),
        'unread_notifications': unread_notifications,
        'unread_count': unread_count,
        'recent_announcements': relevant_announcements,
    }
    # Build enrolled_courses list for dashboard template from enrollments
    enrolled_courses = []
    # Exclude specific subject cards from the student's dashboard
    exclude_codes = {'ART-G1', 'ART101', 'MATH-G1', 'SCI-G1', 'SCI101'}
    exclude_names = {'English Reading'}

    for enr in student_enrollments:
        subj = enr.subject
        subj_code = getattr(subj, 'code', None)
        subj_name = getattr(subj, 'name', None)
        if (subj_code and subj_code in exclude_codes) or (subj_name and subj_name in exclude_names):
            # Skip showing this subject on the dashboard
            continue
        enrolled_courses.append({
            'name': subj.name,
            'code': subj.code,
            'instructor': subj.instructor.user.get_full_name() if getattr(subj, 'instructor', None) else 'TBA',
            'schedule': subj.schedule_display,
            'is_auto_assigned': getattr(enr, 'is_auto_assigned', False),
            'status': getattr(enr, 'status', None),
            'enrollment': enr,
        })
    context['enrolled_courses'] = enrolled_courses
    # If student has no enrollments, provide assigned/core subjects for their grade
    if student_enrollments.count() == 0:
        assigned = get_assigned_subjects_for_student(request.user)
        if assigned:
            # Provide subjects list expected by template as `enrolled_courses`
            context['enrollments'] = assigned
            context['assigned_only'] = True
            context['total_subjects'] = len(assigned)
            # Map assigned pseudo-enrollments to subject-like dicts for the dashboard
            enrolled_courses = []
            for a in assigned:
                subj = a.subject if hasattr(a, 'subject') else a
                subj_code = getattr(subj, 'code', None)
                subj_name = getattr(subj, 'name', None)
                if (subj_code and subj_code in exclude_codes) or (subj_name and subj_name in exclude_names):
                    continue
                enrolled_courses.append({
                    'name': subj.name,
                    'code': subj.code,
                    'instructor': getattr(subj, 'instructor', None).user.get_full_name() if getattr(subj, 'instructor', None) else 'TBA',
                    'schedule': subj.schedule_display,
                    'is_auto_assigned': True,
                })
            context['enrolled_courses'] = enrolled_courses
    return render(request, 'students/student_dashboard.html', context)

@student_required
def subject_registration(request):
    # Get enrolled subject IDs to exclude them from available subjects
    enrolled_subject_ids = Enrollment.objects.filter(
        student=request.user
    ).values_list('subject_id', flat=True)
    
    # Get available subjects (not enrolled in) with enrollment count
    available_subjects = Subject.objects.filter(
        is_active=True
    ).exclude(
        id__in=enrolled_subject_ids
    ).annotate(
        current_enrollment=Count('enrollments')
    )
    
    # Determine current academic year / semester / grade from student profile
    student_profile = getattr(request.user, 'studentprofile', None)
    if student_profile:
        current_academic_year = student_profile.academic_year
        current_semester = student_profile.current_semester
        current_grade = student_profile.grade_level
    else:
        # sensible defaults
        current_academic_year = getattr(settings, 'DEFAULT_ACADEMIC_YEAR', '2024-2025')
        current_semester = getattr(settings, 'DEFAULT_SEMESTER', 'first')
        current_grade = 1

    # Allow optional grade selection via GET param to view registration for other grades
    requested_grade = request.GET.get('grade')
    if requested_grade:
        try:
            current_grade = int(requested_grade)
        except ValueError:
            pass

    # Filter available subjects to the selected/current grade
    try:
        available_subjects = available_subjects.filter(grade_level=current_grade)
    except Exception:
        # if current_grade is invalid, fall back to showing all active subjects
        pass

    # Get student's current enrollments
    student_enrollments = Enrollment.objects.filter(
        student=request.user
    ).select_related('subject')
    
    enrolled_subjects = student_enrollments.filter(status__in=['approved', 'pending'])

    # If no enrolled subjects found, provide assigned/core subjects for display
    assigned_only = False
    if not enrolled_subjects.exists():
        assigned = get_assigned_subjects_for_student(request.user, grade_level_override=current_grade)
        if assigned:
            # Optionally persist as Enrollment rows if enabled in settings
            if getattr(settings, 'AUTO_CREATE_ENROLLMENTS', False):
                # Create Enrollment rows (status='pending') for each assigned subject if not exists
                created = 0
                failures = []
                for a in assigned:
                    subj = a.subject
                    try:
                        exists = Enrollment.objects.filter(
                            student=request.user,
                            subject=subj,
                            academic_year=current_academic_year,
                            semester=current_semester
                        ).exists()
                        if not exists:
                            Enrollment.objects.create(
                                student=request.user,
                                subject=subj,
                                academic_year=current_academic_year,
                                semester=current_semester,
                                status='pending',
                                is_auto_assigned=True
                            )
                            created += 1
                    except Exception as e:
                        failures.append((subj, str(e)))

                # Reload enrolled_subjects from DB to show persisted rows
                student_enrollments = Enrollment.objects.filter(student=request.user).select_related('subject')
                enrolled_subjects = student_enrollments.filter(status__in=['approved', 'pending'])
                assigned_only = True
            else:
                enrolled_subjects = assigned
                assigned_only = True
    
    if request.method == 'POST':
        subject_ids = request.POST.getlist('subject_ids')
        
        if subject_ids:
            success_count = 0
            for subject_id in subject_ids:
                try:
                    subject = Subject.objects.get(id=subject_id, is_active=True)
                    
                    # Check if already enrolled
                    if not Enrollment.objects.filter(student=request.user, subject=subject).exists():
                        # Ensure subject grade level matches student's grade to avoid model ValidationError
                        student_grade = getattr(student_profile, 'grade_level', None) if student_profile else None

                        if student_grade is not None and subject.grade_level != student_grade:
                            messages.error(request, f"Cannot register {subject.name}: Subject is for Grade {subject.grade_level} but you are Grade {student_grade}.")
                            continue

                        # Check capacity
                        current_enroll_count = Enrollment.objects.filter(
                            subject=subject, 
                            status__in=['approved', 'pending']
                        ).count()

                        try:
                            if current_enroll_count < subject.max_capacity:
                                Enrollment.objects.create(
                                    student=request.user,
                                    subject=subject,
                                    status='pending',
                                    academic_year=current_academic_year,
                                    semester=current_semester
                                )
                                success_count += 1
                                messages.success(request, f'Successfully registered for {subject.name}. Waiting for approval.')
                            else:
                                # Add to waitlist if subject is full
                                Enrollment.objects.create(
                                    student=request.user,
                                    subject=subject,
                                    status='waitlisted'
                                )
                                messages.info(request, f'Subject {subject.name} is full. You have been added to the waitlist.')
                        except ValidationError as ve:
                            messages.error(request, f'Failed to register {subject.name}: {"; ".join(ve.messages) if hasattr(ve, "messages") else str(ve)}')
                        except IntegrityError as ie:
                            messages.error(request, f'Failed to register {subject.name}: {str(ie)}')
                    else:
                        messages.warning(request, f'You are already enrolled in {subject.name}.')
                        
                except Subject.DoesNotExist:
                    messages.error(request, "Invalid subject selected.")
            
            if success_count > 0:
                messages.success(request, f'Successfully registered for {success_count} subject(s)!')
            return redirect('subject_registration')
    
    context = {
        'available_subjects': available_subjects,
        'enrolled_subjects': enrolled_subjects,
        'enrolled_subject_ids': list(enrolled_subject_ids),
        'enrollments': student_enrollments,
        'current_academic_year': current_academic_year,
        'current_semester': current_semester,
        'current_grade': current_grade,
        'grade_choices': list(range(1, 9)),
    }
    if assigned_only:
        context['assigned_only'] = True
    return render(request, 'students/subject_registration.html', context)

@student_required
def view_transcripts(request):
    """View student transcript with assigned subjects and teacher-filled results"""
    try:
        # Get student profile
        if not hasattr(request.user, 'studentprofile'):
            messages.error(request, "Student profile not found. Please contact administration.")
            return redirect('student_dashboard')
        
        student_profile = request.user.studentprofile
        student = request.user
        
        # Get all enrollments (assigned subjects) with results filled by teachers
        enrollments = Enrollment.objects.filter(
            student=student
        ).select_related('subject', 'subject__instructor__user').order_by('academic_year', 'semester')
        
        # Import compute_numeric_scores from users.views
        from users.views import compute_numeric_scores
        score_map, total_result, graded_count, average_result = compute_numeric_scores(student, enrollments)
        
        transcript_data = []
        total_score = 0
        count = 0
        
        for enrollment in enrollments:
            # Get numeric score from score_map
            numeric_score = score_map.get(enrollment.id)
            
            # Get subject info
            subject = enrollment.subject
            teacher_name = "TBA"
            if subject.instructor and subject.instructor.user:
                teacher_name = subject.instructor.user.get_full_name() or subject.instructor.user.username
            
            # Only include subjects with results (filled by teachers)
            if numeric_score is not None:
                numeric_score = float(numeric_score)
                
                # Convert numeric score to letter grade
                if numeric_score >= 90:
                    letter_grade = 'A'
                elif numeric_score >= 80:
                    letter_grade = 'B'
                elif numeric_score >= 70:
                    letter_grade = 'C'
                elif numeric_score >= 60:
                    letter_grade = 'D'
                else:
                    letter_grade = 'F'
                
                transcript_data.append({
                    'subject_code': getattr(subject, 'code', ''),
                    'subject_name': subject.name,
                    'grade': letter_grade,
                    'score': round(numeric_score, 2),
                    'academic_year': getattr(enrollment, 'academic_year', 'N/A'),
                    'semester': getattr(enrollment, 'get_semester_display', lambda: 'N/A')(),
                    'teacher': teacher_name,
                })
                
                total_score += numeric_score
                count += 1
        
        # Calculate average
        average_score = round(total_score / count, 2) if count > 0 else 0
        
        # Get class rank if available
        grade_level = getattr(student_profile, 'grade_level', None)
        class_rank = None
        if grade_level:
            try:
                # Get all students in same grade level
                from users.views import compute_numeric_scores
                peers = User.objects.filter(
                    role='student',
                    studentprofile__grade_level=grade_level
                ).prefetch_related('subject_enrollments', 'subject_enrollments__subject', 'studentprofile')
                
                # Calculate ranks
                peer_data = []
                for peer in peers:
                    peer_enrollments = Enrollment.objects.filter(student=peer)
                    _, peer_total, _, peer_avg = compute_numeric_scores(peer, peer_enrollments)
                    if peer_avg is not None:
                        peer_data.append({
                            'student_id': peer.id,
                            'average': peer_avg
                        })
                
                # Sort by average descending
                peer_data.sort(key=lambda x: x['average'], reverse=True)
                
                # Find rank
                for idx, peer in enumerate(peer_data, start=1):
                    if peer['student_id'] == student.id:
                        class_rank = idx
                        break
            except Exception as e:
                print(f"Error calculating class rank: {e}")
                class_rank = None
        
        context = {
            'student': student,
            'student_profile': student_profile,
            'transcript_data': transcript_data,
            'total_result': round(total_result, 2),
            'average_result': average_result or average_score,
            'class_rank': class_rank,
            'graded_count': count,
        }
        
        return render(request, 'students/view_transcripts.html', context)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        messages.error(request, f"Error loading transcript: {str(e)}")
        return redirect('student_dashboard')

@student_required
def download_transcript_pdf(request):
    """Download student transcript as PDF"""
    try:
        # Check if ReportLab is available
        try:
            import io
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib import colors
            REPORTLAB_AVAILABLE = True
        except ImportError:
            from django.http import HttpResponse
            return HttpResponse("PDF generation requires ReportLab. Install with `pip install reportlab`.", status=503)
        
        # Get student profile
        if not hasattr(request.user, 'studentprofile'):
            from django.http import HttpResponse
            return HttpResponse("Student profile not found.", status=404)
        
        student_profile = request.user.studentprofile
        student = request.user
        
        # Get all enrollments with results
        enrollments = Enrollment.objects.filter(
            student=student
        ).select_related('subject', 'subject__instructor__user').order_by('academic_year', 'semester')
        
        # Import compute_numeric_scores
        from users.views import compute_numeric_scores
        score_map, total_result, graded_count, average_result = compute_numeric_scores(student, enrollments)
        
        # Build PDF
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
        <b>Student ID:</b> {getattr(student_profile, 'student_id', 'N/A')}<br/>
        <b>Grade Level:</b> Grade {getattr(student_profile, 'grade_level', 'N/A')}<br/>
        <b>Academic Year:</b> {getattr(student_profile, 'academic_year', 'N/A')}<br/>
        <b>Generated Date:</b> {timezone.now().strftime('%Y-%m-%d')}
        """
        story.append(Paragraph(student_info, styles["Normal"]))
        story.append(Spacer(1, 20))
        
        # Build transcript data
        transcript_data = []
        for enrollment in enrollments:
            numeric_score = score_map.get(enrollment.id)
            if numeric_score is not None:
                subject = enrollment.subject
                teacher_name = "TBA"
                if subject.instructor and subject.instructor.user:
                    teacher_name = subject.instructor.user.get_full_name() or subject.instructor.user.username
                
                transcript_data.append({
                    'academic_year': str(getattr(enrollment, 'academic_year', 'N/A')),
                    'semester': str(getattr(enrollment, 'get_semester_display', lambda: 'N/A')()),
                    'subject_code': getattr(subject, 'code', 'N/A'),
                    'subject_name': subject.name,
                    'score': round(float(numeric_score), 2),
                    'teacher': teacher_name,
                })
        
        # Grades Table
        if transcript_data:
            data = [['Academic Year', 'Semester', 'Subject Code', 'Subject Name', 'Result (out of 100)', 'Teacher']]
            
            for item in transcript_data:
                data.append([
                    item['academic_year'],
                    item['semester'],
                    item['subject_code'],
                    item['subject_name'],
                    str(int(item['score'])),
                    item['teacher']
                ])
            
            # Create table
            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
            ]))
            story.append(table)
            story.append(Spacer(1, 20))
            
            # Calculate class rank
            class_rank = None
            grade_level = getattr(student_profile, 'grade_level', None)
            if grade_level:
                try:
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
                        if peer['student_id'] == student.id:
                            class_rank = idx
                            break
                except Exception:
                    pass
            
            # Summary Section
            summary_data = [
                ['Total Result', str(int(total_result)) if total_result > 0 else 'N/A'],
                ['Average Result', f"{average_result:.1f} / 100" if average_result else 'N/A'],
                ['Class Rank', f"#{class_rank}" if class_rank else 'N/A']
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
            story.append(Paragraph("No transcript data available.", styles["Normal"]))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        from django.http import HttpResponse
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{student.username}_transcript.pdf"'
        return response
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        from django.http import HttpResponse
        return HttpResponse(f"Error generating PDF: {str(e)}", status=500)

def get_performance_summary(gpa):
    """Get elementary-friendly performance description"""
    if gpa >= 3.5:
        return "🌟 Outstanding! You're doing excellent work!"
    elif gpa >= 3.0:
        return "👍 Very Good! Keep up the great work!"
    elif gpa >= 2.0:
        return "✅ Good job! You're making good progress."
    elif gpa >= 1.0:
        return "📝 Keep practicing! You're getting there."
    else:
        return "💪 Don't give up! Let's work together to improve."

@student_required
def pay_fees(request):
    fee_structures = FeeStructure.objects.filter(is_active=True)
    student_payments = Payment.objects.filter(student=request.user).select_related('fee_structure')
    
    if request.method == 'POST':
        fee_structure_id = request.POST.get('fee_structure_id')
        fee_structure = get_object_or_404(FeeStructure, id=fee_structure_id)
        
        # Check if payment already exists
        if Payment.objects.filter(student=request.user, fee_structure=fee_structure, status='completed').exists():
            messages.warning(request, 'You have already paid this fee.')
        else:
            # Create payment (simplified - integrate with payment gateway in production)
            payment = Payment.objects.create(
                student=request.user,
                fee_structure=fee_structure,
                amount_paid=fee_structure.amount,
                payment_method='Online',
                transaction_id=f"TXN{request.user.id}{timezone.now().timestamp()}",
                status='completed'
            )
            
            messages.success(request, f'Payment of ${fee_structure.amount} completed successfully!')
        
        return redirect('pay_fees')
    
    context = {
        'fee_structures': fee_structures,
        'payments': student_payments,
    }
    return render(request, 'students/pay_fees.html', context)

@student_required
def view_announcements(request):
    """View school announcements relevant to students"""
    try:
        # Get all active announcements first
        all_announcements = Announcement.objects.filter(is_active=True).order_by('-created_at')
        
        # Filter in Python instead of using contains lookup (works better with JSONField)
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
            
            # Check if announcement targets students or is for everyone
            # Empty list or no target_roles means show to all
            if not target_roles or len(target_roles) == 0 or 'student' in target_roles:
                relevant_announcements.append(announcement)
                
    except Exception as e:
        # Fallback: get all active announcements if there's an error
        relevant_announcements = Announcement.objects.filter(is_active=True).order_by('-created_at')
        print(f"Error filtering announcements: {e}")
    
    context = {
        'announcements': relevant_announcements,
    }
    return render(request, 'students/announcements.html', context)

@student_required
def interact_with_ai(request):
    # Get or create conversation
    conversation, created = AIConversation.objects.get_or_create(user=request.user)
    messages = AIMessage.objects.filter(conversation=conversation).order_by('created_at')
    
    if request.method == 'POST':
        user_message = request.POST.get('message')
        
        if user_message:
            # Save user message
            AIMessage.objects.create(
                conversation=conversation,
                content=user_message,
                is_user=True
            )
            
            # Generate AI response (simplified - integrate with actual AI in production)
            ai_response = generate_ai_response(user_message, request.user)
            
            # Save AI response
            AIMessage.objects.create(
                conversation=conversation,
                content=ai_response,
                is_user=False
            )
            
            return redirect('interact_with_ai')
    
    context = {
        'conversation': conversation,
        'messages': messages,
    }
    return render(request, 'students/ai_advisor.html', context)

def generate_ai_response(message, user):
    """Generate AI response with access to real student data"""
    message_lower = message.lower()
    
    # Get student profile and data
    try:
        student_profile = user.studentprofile
        grade_level = getattr(student_profile, 'grade_level', None)
        
        # Get enrollments and scores
        enrollments = Enrollment.objects.filter(student=user).select_related('subject')
        from users.views import compute_numeric_scores
        score_map, total_result, graded_count, average_result = compute_numeric_scores(user, enrollments)
        
        # Build subject results list
        subject_results = []
        for enrollment in enrollments:
            score = score_map.get(enrollment.id)
            if score is not None:
                subject_results.append({
                    'name': enrollment.subject.name,
                    'score': float(score)
                })
    except Exception as e:
        student_profile = None
        grade_level = None
        subject_results = []
        average_result = None
    
    # Handle different types of queries
    if 'result' in message_lower or 'score' in message_lower or 'grade' in message_lower or 'how am i doing' in message_lower:
        if subject_results:
            response = f"Great question! Here are your results:\n\n"
            for subj in subject_results:
                grade_emoji = "🌟" if subj['score'] >= 90 else "👍" if subj['score'] >= 80 else "📚" if subj['score'] >= 70 else "💪"
                response += f"{grade_emoji} {subj['name']}: {subj['score']:.0f}/100\n"
            if average_result:
                response += f"\nYour average score is {average_result:.1f}/100. "
                if average_result >= 90:
                    response += "Excellent work! You're doing amazing! 🌟"
                elif average_result >= 80:
                    response += "Great job! Keep up the good work! 👍"
                elif average_result >= 70:
                    response += "Good progress! Keep studying and you'll improve even more! 📚"
                else:
                    response += "Keep practicing! I'm here to help you improve! 💪"
            return response
        else:
            return "You haven't received grades yet, but I'm here to help you prepare! What subject would you like help with?"
    
    elif 'subject' in message_lower or 'class' in message_lower or 'course' in message_lower:
        if grade_level:
            grade_subjects = {
                1: "Reading, Math (counting, adding), Science (animals, plants), Art, Music",
                2: "Reading & Writing, Math (addition, subtraction), Science (weather, animals), Social Studies",
                3: "Reading & Writing, Math (multiplication basics), Science (plants, animals, weather), Social Studies (communities)",
                4: "Reading & Writing, Math (multiplication, division), Science (ecosystems), Social Studies (history basics)",
                5: "Reading & Writing, Math (fractions, decimals), Science (matter, energy), Social Studies (geography)",
                6: "Reading & Writing, Math (pre-algebra), Science (earth science), Social Studies (world cultures)",
                7: "Reading & Writing, Math (algebra basics), Science (life science), Social Studies (history)",
                8: "Reading & Writing, Math (algebra), Science (physical science), Social Studies (civics)"
            }
            subjects = grade_subjects.get(grade_level, "various subjects")
            return f"For Grade {grade_level}, you'll study: {subjects}. Which subject interests you most?"
        return "I can help you learn about different subjects! What would you like to know?"
    
    elif 'study' in message_lower or 'learn' in message_lower or 'how to' in message_lower:
        study_tips = [
            "📚 Study Tips:\n• Find a quiet place to study\n• Take breaks every 20-30 minutes\n• Use flashcards for memorization\n• Practice problems daily\n• Ask questions when you don't understand!",
            "💡 Learning Tips:\n• Read your notes out loud\n• Draw pictures to remember things\n• Teach someone else what you learned\n• Review a little bit every day\n• Make learning fun with games!",
            "🎯 Success Tips:\n• Set small goals each day\n• Celebrate your progress\n• Stay organized with a planner\n• Get enough sleep\n• Eat healthy snacks while studying!"
        ]
        import random
        return random.choice(study_tips)
    
    elif 'recommend' in message_lower or 'suggest' in message_lower:
        if subject_results:
            # Find subjects that need improvement
            weak_subjects = [s for s in subject_results if s['score'] < 70]
            if weak_subjects:
                response = f"I recommend focusing on these subjects to improve:\n"
                for subj in weak_subjects:
                    response += f"• {subj['name']}: Practice more, ask your teacher for help, and review your notes daily.\n"
                return response
            else:
                return "You're doing great in all subjects! Keep up the excellent work! 🌟"
        return "I'd be happy to give recommendations! What subject are you interested in?"
    
    elif any(word in message_lower for word in ['math', 'mathematics', 'numbers', 'counting']):
        return "Math is fun! Here are some tips:\n• Practice counting every day\n• Use objects to help you add and subtract\n• Play math games\n• Review your multiplication tables\n• Ask for help when you're stuck!\n\nWhat math topic would you like help with?"
    
    elif any(word in message_lower for word in ['reading', 'read', 'book', 'story']):
        return "Reading is wonderful! Tips to improve:\n• Read for 20 minutes every day\n• Sound out words you don't know\n• Ask questions about the story\n• Practice writing your own stories\n• Visit the library often!\n\nWhat would you like to read about?"
    
    elif any(word in message_lower for word in ['science', 'experiment', 'animals', 'plants']):
        return "Science is exciting! Here's how to learn:\n• Observe the world around you\n• Ask \"why\" questions\n• Do simple experiments at home\n• Draw what you see\n• Keep a science journal!\n\nWhat science topic interests you?"
    
    elif 'hello' in message_lower or 'hi' in message_lower or 'hey' in message_lower:
        if grade_level:
            return f"Hello! I'm your learning helper for Grade {grade_level}! I can help you with:\n• Your subject results\n• Study tips\n• Homework help\n• Subject recommendations\n\nWhat would you like to know?"
        return "Hello! I'm your learning helper! I can help with homework, study tips, and answer questions about your subjects. What would you like help with?"
    
    else:
        # Default helpful response
        default_responses = [
            "I'm here to help you learn! You can ask me about:\n• Your grades and results\n• Study tips\n• Subject recommendations\n• Homework help\n• How to improve in specific subjects",
            "That's a great question! I can help you with school subjects, study strategies, or your academic progress. What would you like to know?",
            "Learning is an adventure! I can help you understand your results, suggest study methods, or answer questions about your subjects. What interests you?"
        ]
        import random
        return random.choice(default_responses)

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

class StudentViewSet(viewsets.ModelViewSet):
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Return only the student profile for the current user
        return Student.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def subject_registration(self, request):
        """
        GET /api/students/subject_registration/
        Returns available subjects for registration
        """
        try:
            student = request.user.student_profile
            
            # Get available subjects (subjects not enrolled by this student)
            available_subjects = Subject.objects.exclude(
                enrollments__student=student
            ).filter(is_active=True)
            
            # Get currently enrolled subjects
            enrolled_subjects = Subject.objects.filter(
                enrollments__student=student
            )
            
            available_serializer = SubjectSerializer(available_subjects, many=True)
            enrolled_serializer = SubjectSerializer(enrolled_subjects, many=True)
            
            return Response({
                'available_subjects': available_serializer.data,
                'enrolled_subjects': enrolled_serializer.data,
                'total_available': available_subjects.count(),
                'total_enrolled': enrolled_subjects.count()
            })
            
        except AttributeError:
            return Response(
                {'error': 'Student profile not found. Please complete your student profile.'},
                status=status.HTTP_400_BAD_REQUEST
            )

@student_required
def get_notifications_ajax(request):
    """AJAX endpoint to fetch notifications for refresh"""
    from notifications.models import Notification
    try:
        notifications = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')[:10]
        notifications_data = []
        for notif in notifications:
            notifications_data.append({
                'id': notif.id,
                'title': notif.title or 'Notification',
                'message': notif.message or '',
                'created_at': notif.created_at.strftime('%B %d, %Y at %I:%M %p'),
                'is_read': notif.is_read,
            })
        return JsonResponse({
            'success': True,
            'notifications': notifications_data,
            'count': len(notifications_data),
            'unread_count': Notification.objects.filter(user=request.user, is_read=False).count()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@student_required
def get_announcements_ajax(request):
    """AJAX endpoint to fetch announcements for refresh"""
    try:
        all_announcements = Announcement.objects.filter(is_active=True).order_by('-created_at')[:10]
        relevant_announcements = []
        for announcement in all_announcements:
            target_roles = getattr(announcement, 'target_roles', [])
            if isinstance(target_roles, str):
                try:
                    target_roles = json.loads(target_roles)
                except:
                    target_roles = [role.strip() for role in target_roles.split(',') if role.strip()]
            elif not isinstance(target_roles, list):
                target_roles = []
            if not target_roles or len(target_roles) == 0 or 'student' in target_roles:
                relevant_announcements.append({
                    'id': announcement.id,
                    'title': announcement.title,
                    'content': announcement.content,
                    'created_at': announcement.created_at.strftime('%B %d, %Y at %I:%M %p'),
                })
        return JsonResponse({
            'success': True,
            'announcements': relevant_announcements,
            'count': len(relevant_announcements)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
    
    @action(detail=False, methods=['get'])
    def subject_registration(self, request):
        """Temporary redirect to subject_registration"""
        return Response({
            "message": "This endpoint has been moved to subject_registration",
            "new_endpoint": "/api/students/subject_registration/",
            "note": "Please update your application to use the new endpoint"
        })

def debug_urls(request):
    return JsonResponse({
        'available_urls': [
            '/api/students/subject_registration/',
            '/api/students/',
        ],
        'requested_url': request.build_absolute_uri(),
        'message': 'Use /api/students/subject_registration/ instead of course-registration'
    })
    