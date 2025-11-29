from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, Count
from django.db.models import Avg
from users.decorators import teacher_required, registrar_required
from users.models import User
from subjects.models import Subject, Enrollment
from ranks.models import Grade, rank_students_for_subject
from ranks.forms import GradeForm
from django.http import JsonResponse
from django.db.utils import OperationalError
from django.views.decorators.http import require_POST
from .forms import BulkAssignForm
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from notifications.models import Notification


def get_teacher_profile(user):
    """Ensure a Teacher profile exists for the given User. Returns Teacher instance or None."""
    try:
        from subjects.models import Teacher as TeacherModel
        teacher_obj, created = TeacherModel.objects.get_or_create(
            user=user,
            defaults={
                'teacher_id': f'T{user.id}',
                'department': '',
                'phone_number': '',
                'office_location': ''
            }
        )
        return teacher_obj
    except Exception:
        return None


def _get_current_academic_year():
    import datetime
    now = datetime.datetime.now()
    if now.month >= 8:
        return f"{now.year}-{now.year + 1}"
    else:
        return f"{now.year - 1}-{now.year}"


def _get_current_semester():
    import datetime
    now = datetime.datetime.now()
    if 1 <= now.month <= 5:
        return 'second'
    elif 6 <= now.month <= 7:
        return 'summer'
    else:
        return 'first'


def enroll_students_for_subject(subject, academic_year=None, semester=None, status='approved'):
    """Enroll all students in the system matching subject.grade_level into this subject
    for the provided academic_year and semester if they are not already enrolled."""
    if academic_year is None:
        academic_year = _get_current_academic_year()
    if semester is None:
        semester = _get_current_semester()

    # find students with matching grade level
    students = User.objects.filter(role='student', studentprofile__grade_level=subject.grade_level)
    enrolled = 0
    for student in students:
        try:
            existing = Enrollment.objects.filter(student=student, subject=subject, academic_year=academic_year, semester=semester).first()
            if existing:
                # If there's an existing enrollment (e.g., pending), promote it to the desired status
                if existing.status != status:
                    existing.status = status
                    existing.is_auto_assigned = True
                    try:
                        existing.save()
                    except Exception:
                        pass
                    enrolled += 1
                continue

            Enrollment.objects.create(
                student=student,
                subject=subject,
                academic_year=academic_year,
                semester=semester,
                status=status,
                is_auto_assigned=True
            )
            enrolled += 1
        except Exception:
            continue
    return enrolled

@teacher_required
def teacher_dashboard(request):
    # allow optional filtering by grade_level, academic_year and semester via GET params
    grade_level_filter = request.GET.get('grade_level')
    academic_year_filter = request.GET.get('academic_year')
    semester_filter = request.GET.get('semester')
    # default to current term when not provided
    if not academic_year_filter:
        academic_year_filter = _get_current_academic_year()
    if not semester_filter:
        semester_filter = _get_current_semester()

    # annotate each subject (assigned to this teacher) with the number of approved/active students for the selected term
    teacher_qs = Subject.objects.filter(instructor__user=request.user, is_active=True)
    if grade_level_filter:
        try:
            teacher_qs = teacher_qs.filter(grade_level=int(grade_level_filter))
        except Exception:
            pass
    teacher_subjects = teacher_qs.annotate(
        student_count=Count('enrollments', filter=Q(enrollments__status__in=['approved', 'active'], enrollments__academic_year=academic_year_filter, enrollments__semester=semester_filter))
    )

    total_students = Enrollment.objects.filter(
        subject__instructor__user=request.user,
        status__in=['approved', 'active'],
        academic_year=academic_year_filter,
        semester=semester_filter
    ).count()

    # pending scores across all subjects for this teacher
    try:
        pending = Grade.objects.filter(
            subject__instructor__user=request.user,
            score__isnull=True
        ).count()
    except OperationalError:
        pending = 0

    # per-subject pending counts (dictionary subject_id -> pending_count)
    per_subject_pending = {}
    try:
        pending_qs = Grade.objects.filter(subject__instructor__user=request.user, score__isnull=True).values('subject').annotate(count=Count('id'))
        per_subject_pending = {p['subject']: p['count'] for p in pending_qs}
    except OperationalError:
        per_subject_pending = {}

    # attach pending_count to each subject for easy template access
    for s in teacher_subjects:
        s.pending_count = per_subject_pending.get(s.id, 0)

    # subjects that are currently unassigned (available for claiming)
    available_qs = Subject.objects.filter(instructor__isnull=True, is_active=True)
    if grade_level_filter:
        try:
            available_qs = available_qs.filter(grade_level=int(grade_level_filter))
        except Exception:
            pass
    # academic year and semester may be represented on the Subject model differently in some projects
    # attempt to filter if those fields exist
    if academic_year_filter and hasattr(Subject, 'academic_year'):
        available_qs = available_qs.filter(academic_year=academic_year_filter)
    if semester_filter and hasattr(Subject, 'semester'):
        available_qs = available_qs.filter(semester__iexact=semester_filter)

    available_subjects = available_qs.annotate(
        student_count=Count('enrollments', filter=Q(enrollments__status__in=['approved','active'], enrollments__academic_year=academic_year_filter, enrollments__semester=semester_filter))
    )

    # distinct students across this teacher's subjects
    # Respect academic year / semester filters when listing students
    # use the already-determined filters for term
    ay = academic_year_filter
    sem = semester_filter
    enrolled_qs = Enrollment.objects.filter(subject__in=teacher_subjects, status__in=['approved', 'active'], academic_year=ay, semester=sem).select_related('student')
    distinct_students = {}
    for en in enrolled_qs:
        distinct_students[en.student.id] = en.student

    # compute per-student average across this teacher's subjects
    student_averages = {}
    for student_id, student in distinct_students.items():
        # restrict averaging to this term: find which of the teacher's subjects this student is enrolled in for the term
        subject_ids_for_term = Enrollment.objects.filter(student__id=student_id, subject__in=teacher_subjects, academic_year=ay, semester=sem, status__in=['approved', 'active']).values_list('subject_id', flat=True)
        if subject_ids_for_term:
            avg = Grade.objects.filter(student__id=student_id, subject__id__in=subject_ids_for_term).aggregate(avg=Avg('score'))['avg']
        else:
            avg = None
        student_averages[student_id] = {'student': student, 'average': round(avg, 2) if avg is not None else None}

    # compute ranking (higher average -> better rank). Students with None average go last.
    ranked = sorted([{'id': sid, 'avg': data['average'], 'student': data['student']} for sid, data in student_averages.items()], key=lambda x: (-(x['avg'] or -1), x['student'].get_full_name()))
    # assign ranks (ties receive same rank)
    last_avg = None
    rank = 0
    ties = 0
    for i, item in enumerate(ranked, start=1):
        if item['avg'] is None:
            item['rank'] = None
            continue
        if item['avg'] != last_avg:
            rank = i
            last_avg = item['avg']
        item['rank'] = rank

    # build per-subject averages
    subject_averages = {}
    for s in teacher_subjects:
        avg = Grade.objects.filter(subject=s).aggregate(avg=Avg('score'))['avg']
        subject_averages[s.id] = round(avg, 2) if avg is not None else None
    # Get unread notifications for the teacher
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')[:5]
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    
    # term filters (prefer GET, else current)
    academic_year = request.GET.get('academic_year') or _get_current_academic_year()
    semester = request.GET.get('semester') or _get_current_semester()

    # grade choices (use Subject model choices) and academic year choices for the filter UI
    try:
        grade_choices = Subject.GRADE_LEVEL_CHOICES
    except Exception:
        grade_choices = []

    try:
        cur_start = int(_get_current_academic_year().split('-')[0])
        academic_year_choices = [f"{y}-{y+1}" for y in range(cur_start - 3, cur_start + 1)]
    except Exception:
        academic_year_choices = [academic_year]

    context = {
        'teacher_subjects': teacher_subjects,
        'total_students': total_students,
        'pending_scores': pending,
        'available_subjects': available_subjects,
        'filter_grade_level': grade_level_filter,
        'filter_academic_year': academic_year_filter,
        'filter_semester': semester_filter,
        'display_academic_year': academic_year_filter,
        'display_semester': semester_filter,
        'grade_choices': grade_choices,
        'academic_year_choices': academic_year_choices,
        'selected_grade_level': grade_level_filter,
        'selected_academic_year': academic_year,
        'selected_semester': semester,
        'num_subjects': teacher_subjects.count(),
        'distinct_student_count': len(distinct_students),
        'student_averages': student_averages,
        'student_ranking': ranked,
        'unread_notifications': unread_notifications,
        'unread_count': unread_count,
    }
    return render(request, 'teachers/teacher_dashboard.html', context)

@registrar_required
def claim_subject(request, subject_id):
    """Registrar-only: assign a subject to a teacher.

    POST params: teacher_user_id (user id of teacher)
    """
    if request.method != 'POST':
        messages.error(request, 'Invalid request method for assigning subjects.')
        return redirect('registrar_dashboard')

    subject = get_object_or_404(Subject, id=subject_id)
    teacher_user_id = request.POST.get('teacher_user_id')
    if not teacher_user_id:
        messages.error(request, 'No teacher specified for assignment.')
        return redirect('registrar_dashboard')

    try:
        from subjects.models import Teacher as TeacherModel
        teacher_user = User.objects.get(id=int(teacher_user_id), role='teacher')
        teacher_obj, created = TeacherModel.objects.get_or_create(user=teacher_user, defaults={'teacher_id': f'T{teacher_user.id}', 'department': ''})
    except Exception:
        messages.error(request, 'Teacher not found. Cannot assign subject.')
        return redirect('registrar_dashboard')

    subject.instructor = teacher_obj
    subject.save()
    try:
        enrolled = enroll_students_for_subject(subject)
        if enrolled:
            messages.info(request, f'Auto-enrolled {enrolled} students for {subject.code}.')
    except Exception:
        pass

    messages.success(request, f'Subject {subject.code} assigned to {teacher_user.get_full_name()}.')
    return redirect('registrar_dashboard')


@registrar_required
@require_POST
def assign_subjects_for_term(request):
    """Bulk assign subjects to the logged-in teacher for a given grade/term.

    POST params: grade_level, academic_year, semester
    Only assigns subjects that are active and currently have no instructor.
    """
    form = BulkAssignForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Invalid input for bulk assignment.')
        return redirect('teacher_dashboard')
    grade_level = form.cleaned_data['grade_level']
    academic_year = form.cleaned_data['academic_year']
    semester = form.cleaned_data['semester']

    # Registrar must provide the teacher_user_id in POST
    teacher_user_id = request.POST.get('teacher_user_id')
    if not teacher_user_id:
        messages.error(request, 'Please specify a teacher to assign these subjects to.')
        return redirect('registrar_dashboard')

    try:
        from subjects.models import Teacher as TeacherModel
        teacher_user = User.objects.get(id=int(teacher_user_id), role='teacher')
        teacher_obj, created = TeacherModel.objects.get_or_create(user=teacher_user, defaults={'teacher_id': f'T{teacher_user.id}', 'department': ''})
    except Exception:
        messages.error(request, 'Teacher not found. Cannot assign subjects.')
        return redirect('registrar_dashboard')

    # Find subjects for this grade level and term (term info is not on Subject model,
    # so we filter by grade_level and is_active and only assign if instructor is None)
    subjects_qs = Subject.objects.filter(grade_level=grade_level, is_active=True, instructor__isnull=True)
    assigned = 0
    for subj in subjects_qs:
        # if academic_year/semester provided, only assign if subject has available slots
        try:
            if academic_year and semester:
                if not subj.is_available(academic_year, semester):
                    continue
        except Exception:
            # if subject doesn't support availability checks, continue assigning
            pass

        subj.instructor = teacher_obj
        subj.save()
        try:
            # enroll students for provided term
            enrolled = enroll_students_for_subject(subj, academic_year=academic_year, semester=semester)
            if enrolled:
                messages.info(request, f'Auto-enrolled {enrolled} students for {subj.code}.')
        except Exception:
            pass
        assigned += 1

    messages.success(request, f'Assigned {assigned} subjects for Grade {grade_level} ({academic_year} - {semester}) to {teacher_user.get_full_name()}.')
    return redirect('registrar_dashboard')


@registrar_required
@require_POST
def assign_selected_subjects(request):
    """Assign the list of subject IDs posted by the teacher to themselves.

    POST param: subject_ids (one or more)
    """
    subject_ids = request.POST.getlist('subject_ids')
    if not subject_ids:
        messages.error(request, 'No subjects selected to assign.')
        return redirect('teacher_dashboard')

    # Registrar must provide teacher_user_id
    teacher_user_id = request.POST.get('teacher_user_id')
    if not teacher_user_id:
        messages.error(request, 'Please specify a teacher to assign these subjects to.')
        return redirect('registrar_dashboard')

    try:
        from subjects.models import Teacher as TeacherModel
        teacher_user = User.objects.get(id=int(teacher_user_id), role='teacher')
        teacher_obj, created = TeacherModel.objects.get_or_create(user=teacher_user, defaults={'teacher_id': f'T{teacher_user.id}', 'department': ''})
    except Exception:
        messages.error(request, 'Teacher not found. Cannot assign subjects.')
        return redirect('registrar_dashboard')

    # allow optional academic_year/semester in POST to control enrollments
    academic_year = request.POST.get('academic_year') or None
    semester = request.POST.get('semester') or None

    assigned = 0
    for sid in subject_ids:
        try:
            subj = Subject.objects.get(id=int(sid), is_active=True)
        except Exception:
            continue
        # only assign if currently unassigned
        if subj.instructor is not None:
            continue
        subj.instructor = teacher_obj
        subj.save()
        try:
            enrolled = enroll_students_for_subject(subj, academic_year=academic_year, semester=semester)
            if enrolled:
                messages.info(request, f'Auto-enrolled {enrolled} students for {subj.code}.')
        except Exception:
            pass
        assigned += 1

    messages.success(request, f'Assigned {assigned} selected subjects to {teacher_user.get_full_name()}.')
    return redirect('registrar_dashboard')

@teacher_required
def enter_grades(request):
    teacher_subjects = Subject.objects.filter(instructor__user=request.user, is_active=True)
    selected_subject_id = request.GET.get('subject_id')
    
    if selected_subject_id:
        subject = get_object_or_404(Subject, id=selected_subject_id)
        # Only allow entering grades if the logged-in teacher is the instructor
        if subject.instructor and subject.instructor.user != request.user:
            messages.error(request, 'You are not the instructor for the selected subject.')
            return redirect('teacher_dashboard')
        # Filter enrollments by academic year & semester (default to current)
        academic_year = request.GET.get('academic_year') or _get_current_academic_year()
        semester = request.GET.get('semester') or _get_current_semester()
        enrollments = Enrollment.objects.filter(subject=subject, status__in=['approved', 'active'], academic_year=academic_year, semester=semester).select_related('student')
        
        # load existing grades for this subject to prefill the form
        existing_grades_qs = Grade.objects.filter(subject=subject).select_related('student')
        existing_grades = {g.student.id: g.score for g in existing_grades_qs}
        existing_components = {}
        for g in existing_grades_qs:
            existing_components[g.student.id] = {
                'quiz': getattr(g, 'quiz_score', None),
                'mid': getattr(g, 'mid_score', None),
                'assignment': getattr(g, 'assignment_score', None),
                'final': getattr(g, 'final_exam_score', None),
            }
        # attach component values and current_score to enrollment objects for easy template access
        for en in enrollments:
            en.current_score = existing_grades.get(en.student.id)
            comps = existing_components.get(en.student.id, {})
            en.quiz_score = comps.get('quiz')
            en.mid_score = comps.get('mid')
            en.assignment_score = comps.get('assignment')
            en.final_score = comps.get('final')

        # compute per-student average across this teacher's subjects for the selected term
        student_ids = [en.student.id for en in enrollments]
        student_averages = {}
        try:
            for sid in student_ids:
                subj_ids = Enrollment.objects.filter(student__id=sid, subject__in=teacher_subjects, academic_year=academic_year, semester=semester, status__in=['approved','active']).values_list('subject_id', flat=True)
                if subj_ids:
                    avg = Grade.objects.filter(student__id=sid, subject__id__in=subj_ids).aggregate(avg=Avg('score'))['avg']
                else:
                    avg = None
                student_averages[sid] = round(avg,2) if avg is not None else None
        except Exception:
            student_averages = {sid: None for sid in student_ids}

        # compute ranking for students by their average (higher is better); ties receive same rank
        ranking = []
        for sid, avg in student_averages.items():
            ranking.append({'student_id': sid, 'avg': avg})
        ranking = sorted(ranking, key=lambda x: (-(x['avg'] or -1), x['student_id']))
        last_avg = None
        last_rank = 0
        rank_map = {}
        idx = 0
        for item in ranking:
            idx += 1
            if item['avg'] is None:
                rank = None
            else:
                if item['avg'] == last_avg:
                    rank = last_rank
                else:
                    rank = idx
                    last_rank = rank
                    last_avg = item['avg']
            rank_map[item['student_id']] = rank

        # attach average and rank to enrollments for template
        for en in enrollments:
            en.average = student_averages.get(en.student.id)
            en.rank = rank_map.get(en.student.id)

        if request.method == 'POST':
            updated = 0
            for enrollment in enrollments:
                    # Support component-based input (quiz, mid, assignment, final)
                    quiz_val = request.POST.get(f'quiz_{enrollment.student.id}')
                    mid_val = request.POST.get(f'mid_{enrollment.student.id}')
                    assign_val = request.POST.get(f'assign_{enrollment.student.id}')
                    final_val = request.POST.get(f'final_{enrollment.student.id}')
                    # legacy single score field fallback
                    grade_value = request.POST.get(f'grade_{enrollment.student.id}')

                    # if no inputs provided, skip
                    if not any([quiz_val, mid_val, assign_val, final_val, grade_value]):
                        continue

                    def parse_int(v, default=None):
                        if v is None or v == '':
                            return default
                        try:
                            return int(float(v))
                        except Exception:
                            return default

                    quiz = parse_int(quiz_val)
                    mid = parse_int(mid_val)
                    assignment = parse_int(assign_val)
                    final = parse_int(final_val)

                    override_avg_val = request.POST.get(f'avg_{enrollment.student.id}')
                    if quiz is None and mid is None and assignment is None and final is None and grade_value:
                        # legacy path: use single score field
                        total = parse_int(grade_value, 0)
                        quiz = mid = assignment = final = None
                    else:
                        # if override average provided (teacher manually edited average), use it to set total
                        if override_avg_val is not None and override_avg_val != '':
                            parsed_override = parse_int(override_avg_val, None)
                            if parsed_override is not None:
                                total = max(0, min(100, parsed_override))
                        else:
                            # clamp components to their max values and treat None as 0
                            quiz = 0 if quiz is None else max(0, min(5, quiz))
                            mid = 0 if mid is None else max(0, min(25, mid))
                            assignment = 0 if assignment is None else max(0, min(20, assignment))
                            final = 0 if final is None else max(0, min(50, final))
                            total = quiz + mid + assignment + final

                    # Clamp total 0-100
                    if total < 0:
                        total = 0
                    if total > 100:
                        total = 100

                    try:
                        grade_obj, created = Grade.objects.get_or_create(
                            student=enrollment.student,
                            subject=subject,
                            defaults={'score': total, 'quiz_score': quiz if quiz is not None else None, 'mid_score': mid if mid is not None else None, 'assignment_score': assignment if assignment is not None else None, 'final_exam_score': final if final is not None else None}
                        )
                    except OperationalError:
                        messages.error(request, 'Database tables for the `ranks` app are missing. Please run `python manage.py migrate`.')
                        return redirect(request.path + f'?subject_id={subject.id}')

                    if not created:
                        grade_obj.score = total
                        # update component fields if provided
                        if quiz is not None:
                            grade_obj.quiz_score = quiz
                        if mid is not None:
                            grade_obj.mid_score = mid
                        if assignment is not None:
                            grade_obj.assignment_score = assignment
                        if final is not None:
                            grade_obj.final_exam_score = final
                        grade_obj.save()

                    # store remarks/result if provided
                    result_val = request.POST.get(f'result_{enrollment.student.id}')
                    if result_val is not None:
                        try:
                            grade_obj.remarks = result_val
                            grade_obj.save()
                        except Exception:
                            pass
                        try:
                            enrollment.result = result_val
                            enrollment.save()
                        except Exception:
                            pass
                    updated += 1

            messages.success(request, f'Scores updated for {updated} students.')
            return redirect(request.path + f'?subject_id={subject.id}')
    else:
        subject = None
        enrollments = []
    
    context = {
        'teacher_subjects': teacher_subjects,
        'selected_subject': subject if selected_subject_id else None,
        'enrollments': enrollments,
        'student_scores': existing_grades if selected_subject_id else {},
    }
    return render(request, 'teachers/enter_grades.html', context)

@teacher_required
def class_rosters(request):
    teacher_subjects = Subject.objects.filter(instructor__user=request.user, is_active=True)
    selected_subject_id = request.GET.get('subject_id')
    
    if selected_subject_id:
        subject = get_object_or_404(Subject, id=selected_subject_id)
        # allow viewing rosters even for unassigned subjects; but if assigned to another teacher, restrict
        if subject.instructor and subject.instructor.user != request.user:
            messages.error(request, 'You are not the instructor for the selected subject.')
            return redirect('teacher_dashboard')
        academic_year = request.GET.get('academic_year') or _get_current_academic_year()
        semester = request.GET.get('semester') or _get_current_semester()
        enrollments = Enrollment.objects.filter(subject=subject, academic_year=academic_year, semester=semester, status__in=['approved', 'active']).select_related('student')
    else:
        subject = None
        enrollments = []
    
    context = {
        'teacher_subjects': teacher_subjects,
        'selected_subject': subject,
        'enrollments': enrollments,
    }
    return render(request, 'teachers/class_rosters.html', context)

@teacher_required
def performance_reports(request):
    teacher_subjects = Subject.objects.filter(instructor__user=request.user, is_active=True)
    selected_subject_id = request.GET.get('subject_id')
    
    if selected_subject_id:
        subject = get_object_or_404(Subject, id=selected_subject_id)
        if subject.instructor and subject.instructor.user != request.user:
            messages.error(request, 'You are not the instructor for the selected subject.')
            return redirect('teacher_dashboard')
        academic_year = request.GET.get('academic_year') or _get_current_academic_year()
        semester = request.GET.get('semester') or _get_current_semester()
        try:
            # Restrict grades to students actually enrolled in this subject for the selected term
            student_ids = Enrollment.objects.filter(subject=subject, academic_year=academic_year, semester=semester, status__in=['approved', 'active']).values_list('student_id', flat=True)
            grades = Grade.objects.filter(subject=subject, student__id__in=student_ids).select_related('student')
        except OperationalError:
            messages.error(request, 'Database tables for the `ranks` app are missing. Please run `python manage.py migrate`.')
            grades = []

        # Calculate numeric statistics (average score out of 100) and ranking
        if grades:
            numeric_scores = [g.score for g in grades if g.score is not None]
            avg_score = sum(numeric_scores) / len(numeric_scores) if numeric_scores else 0
            # build simple distribution buckets
            score_distribution = {
                '90-100': len([s for s in numeric_scores if s >= 90]),
                '80-89': len([s for s in numeric_scores if 80 <= s < 90]),
                '70-79': len([s for s in numeric_scores if 70 <= s < 80]),
                '60-69': len([s for s in numeric_scores if 60 <= s < 70]),
                '0-59': len([s for s in numeric_scores if s < 60]),
            }
            # compute ranks using helper
            subject_ranking = rank_students_for_subject(subject)
        else:
            avg_score = 0
            score_distribution = {}
            subject_ranking = []
    else:
        subject = None
        grades = []
        avg_score = 0
        score_distribution = {}
        subject_ranking = []
    
    context = {
        'teacher_subjects': teacher_subjects,
        'selected_subject': subject,
        'grades': grades,
        'avg_score': round(avg_score, 2),
        'score_distribution': score_distribution,
        'subject_ranking': subject_ranking,
    }
    return render(request, 'teachers/performance_reports.html', context)

@teacher_required
def update_student_grade(request, enrollment_id):
    enrollment = get_object_or_404(Enrollment, id=enrollment_id, subject__instructor__user=request.user)
    
    if request.method == 'POST':
        form = GradeForm(request.POST)
        if form.is_valid():
            try:
                grade, created = Grade.objects.get_or_create(
                    student=enrollment.student,
                    subject=enrollment.subject,
                    defaults={'score': form.cleaned_data.get('score')}
                )
            except OperationalError:
                messages.error(request, 'Database tables for the `ranks` app are missing. Please run `python manage.py migrate`.')
                return redirect('enter_grades')
            if not created:
                for attr, value in form.cleaned_data.items():
                    setattr(grade, attr, value)
                grade.save()
            
            messages.success(request, 'Score updated successfully!')
            return redirect('enter_grades')
    else:
        try:
            try:
                grade = Grade.objects.get(student=enrollment.student, subject=enrollment.subject)
                form = GradeForm(instance=grade)
            except Grade.DoesNotExist:
                form = GradeForm()
        except OperationalError:
            messages.error(request, 'Database tables for the `ranks` app are missing. Please run `python manage.py migrate`.')
            form = GradeForm()
    
    context = {
        'form': form,
        'enrollment': enrollment,
    }
    return render(request, 'teachers/update_grade.html', context)

@teacher_required
def view_student_performance(request, student_id):
    """View individual student performance across all teacher's courses"""
    student = get_object_or_404(User, id=student_id, role='student')
    
    # Get subjects taught by this teacher that the student is enrolled in
    academic_year = request.GET.get('academic_year') or _get_current_academic_year()
    semester = request.GET.get('semester') or _get_current_semester()
    student_courses = Subject.objects.filter(
        instructor__user=request.user,
        enrollments__student=student,
        enrollments__status__in=['approved', 'active'],
        enrollments__academic_year=academic_year,
        enrollments__semester=semester,
    ).distinct()
    
    # Get grades for these courses
    try:
        student_grades = Grade.objects.filter(
            student=student,
            subject__in=student_courses
        ).select_related('subject')
    except OperationalError:
        messages.error(request, 'Database tables for the `ranks` app are missing. Please run `python manage.py migrate`.')
        student_grades = []
    
    context = {
        'student': student,
        'student_subjects': student_courses,
        'student_grades': student_grades,
    }
    return render(request, 'teachers/student_performance.html', context)

@teacher_required
def bulk_grade_upload(request, subject_id):
    """Handle bulk score upload via CSV"""
    subject = get_object_or_404(Subject, id=subject_id, instructor__user=request.user)
    
    if request.method == 'POST' and request.FILES.get('grade_file'):
        grade_file = request.FILES['grade_file']
        # Simple CSV processing (you might want to use csv module for more complex files)
        try:
            # This is a simplified example - implement proper CSV parsing
            lines = grade_file.read().decode('utf-8').split('\n')
            processed_count = 0
            
            for line in lines[1:]:  # Skip header
                if line.strip():
                    parts = line.split(',')
                    if len(parts) >= 2:
                        student_id = parts[0].strip()
                        grade_value = parts[1].strip()
                        
                        # Find student and update grade
                        try:
                            student = User.objects.get(
                                studentprofile__student_id=student_id,
                                role='student'
                            )
                            try:
                                grade, created = Grade.objects.get_or_create(
                                    student=student,
                                    subject=subject,
                                    defaults={'score': None}
                                )
                            except OperationalError:
                                continue
                            if not created:
                                # store the submitted letter grade into remarks for trace
                                grade.remarks = f'entered_grade:{grade_value}'
                                grade.save()
                            if not created:
                                grade.grade = grade_value
                                grade.save()
                            processed_count += 1
                        except User.DoesNotExist:
                            continue
            
            messages.success(request, f'Successfully processed grades for {processed_count} students.')
            
        except Exception as e:
            messages.error(request, f'Error processing file: {str(e)}')
        
        return redirect('enter_grades')
    
    context = {
        'subject': subject,
    }
    return render(request, 'teachers/bulk_grade_upload.html', context)

@teacher_required
def get_subject_statistics(request, subject_id):
    """API endpoint for subject statistics (for charts)"""
    subject = get_object_or_404(Subject, id=subject_id, instructor__user=request.user)
    try:
        grades = Grade.objects.filter(subject=subject)
    except OperationalError:
        messages.error(request, 'Database tables for the `ranks` app are missing. Please run `python manage.py migrate`.')
        grades = []
    
    # Numeric distribution buckets and average score
    numeric_scores = [g.score for g in grades if g.score is not None]
    distribution = {
        '90-100': len([s for s in numeric_scores if s >= 90]),
        '80-89': len([s for s in numeric_scores if 80 <= s < 90]),
        '70-79': len([s for s in numeric_scores if 70 <= s < 80]),
        '60-69': len([s for s in numeric_scores if 60 <= s < 70]),
        '0-59': len([s for s in numeric_scores if s < 60]),
    }
    avg_score = sum(numeric_scores) / len(numeric_scores) if numeric_scores else 0

    data = {
        'score_distribution': distribution,
        'average_score': round(avg_score, 2),
        'total_students': grades.count(),
        'scored_students': len(numeric_scores),
    }
    
    return JsonResponse(data)


@teacher_required
@require_POST
def save_student_score(request):
    """AJAX endpoint to save one student's score and optional result for a subject.

    POST params: student_id, subject_id, score, result (optional)
    Returns JSON {success: true, message: '', avg: <new subject average>} on success.
    """
    student_id = request.POST.get('student_id')
    subject_id = request.POST.get('subject_id')
    # support component fields
    score = request.POST.get('score')
    quiz = request.POST.get('quiz')
    mid = request.POST.get('mid')
    assignment = request.POST.get('assignment')
    final_exam = request.POST.get('final_exam')
    result = request.POST.get('result')

    if not (student_id and subject_id):
        return JsonResponse({'success': False, 'message': 'Missing student_id or subject_id'}, status=400)

    try:
        subject = Subject.objects.get(id=subject_id, instructor__user=request.user)
    except Subject.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Subject not found or you are not the instructor'}, status=403)

    try:
        student = User.objects.get(id=student_id, role='student')
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Student not found'}, status=404)

    try:
        enrollment = Enrollment.objects.get(student=student, subject=subject, status__in=['approved', 'active'])
    except Enrollment.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Student is not enrolled in this subject'}, status=400)

    # validate and store score
    parsed_score = None
    # component parsing
    def parse_int(v, default=None):
        if v is None or v == '':
            return default
        try:
            return int(float(v))
        except Exception:
            return default

    parsed_quiz = parse_int(quiz)
    parsed_mid = parse_int(mid)
    parsed_assignment = parse_int(assignment)
    parsed_final = parse_int(final_exam)
    # support override average (manual edit from UI)
    override_avg = request.POST.get('override_avg')
    try:
        parsed_override = int(float(override_avg)) if override_avg not in (None, '') else None
    except Exception:
        parsed_override = None

    if any(x is not None for x in [parsed_quiz, parsed_mid, parsed_assignment, parsed_final]):
        # clamp components
        parsed_quiz = 0 if parsed_quiz is None else max(0, min(5, parsed_quiz))
        parsed_mid = 0 if parsed_mid is None else max(0, min(25, parsed_mid))
        parsed_assignment = 0 if parsed_assignment is None else max(0, min(20, parsed_assignment))
        parsed_final = 0 if parsed_final is None else max(0, min(50, parsed_final))
        parsed_score = parsed_quiz + parsed_mid + parsed_assignment + parsed_final
        parsed_score = max(0, min(100, parsed_score))
        # if teacher provided an override average, use it instead
        if parsed_override is not None:
            parsed_score = max(0, min(100, parsed_override))
    else:
        if score is not None and score != '':
            try:
                parsed_score = int(float(score))
            except ValueError:
                return JsonResponse({'success': False, 'message': 'Invalid score'}, status=400)
            if parsed_score < 0:
                parsed_score = 0
            if parsed_score > 100:
                parsed_score = 100

    # Create or update Grade (ranks.models.Grade)
    try:
        grade_obj, created = Grade.objects.get_or_create(student=student, subject=subject, defaults={'score': parsed_score})
    except Exception:
        return JsonResponse({'success': False, 'message': 'Database error creating grade'}, status=500)

    # Only overwrite score if a score was provided or computed; otherwise keep existing score
    if not created:
        if parsed_score is not None:
            grade_obj.score = parsed_score
    else:
        # created: ensure score field set (may be None)
        grade_obj.score = parsed_score

    if result is not None:
        grade_obj.remarks = result
    grade_obj.save()

    # Save enrollment-level result
    if result is not None:
        try:
            enrollment.result = result
            enrollment.save()
        except Exception:
            pass

    # compute updated subject average
    avg = Grade.objects.filter(subject=subject, score__isnull=False).aggregate(avg=Avg('score'))['avg']
    avg = round(avg, 2) if avg is not None else None

    return JsonResponse({'success': True, 'message': 'Saved', 'avg': avg})

def get_grade_point(grade_letter):
    """Convert letter grade to grade point - helper function"""
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