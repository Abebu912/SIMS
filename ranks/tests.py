from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from users.models import User, StudentParent, StudentProfile
from subjects.models import Subject, Teacher as TeacherModel, Enrollment
from ranks.models import Grade
from notifications.models import Notification


class FinalSubmissionTest(TestCase):
    def setUp(self):
        # create teacher
        self.teacher = User.objects.create_user(username='teacher1', email='t1@example.com', password='pass')
        self.teacher.role = 'teacher'
        self.teacher.is_approved = True
        self.teacher.save()
        TeacherModel.objects.create(user=self.teacher, teacher_id=f'T{self.teacher.id}', department='Dept')

        # create student and profile
        self.student = User.objects.create_user(username='student1', email='s1@example.com', password='pass')
        self.student.role = 'student'
        self.student.is_approved = True
        self.student.save()
        StudentProfile.objects.create(user=self.student, grade_level=1)

        # create parent and link
        self.parent = User.objects.create_user(username='parent1', email='p1@example.com', password='pass')
        self.parent.role = 'parent'
        self.parent.is_approved = True
        self.parent.save()
        StudentParent.objects.create(parent=self.parent, student=self.student, relationship='Parent', is_primary=True)

        # create subject assigned to teacher
        teacher_profile = TeacherModel.objects.get(user=self.teacher)
        self.subject = Subject.objects.create(name='Test Subject', code='TST100', grade_level=1, instructor=teacher_profile)

        # create enrollment
        self.enrollment = Enrollment.objects.create(student=self.student, subject=self.subject, academic_year='2024-2025', semester='first', status='approved')

        self.client = Client()

    def test_final_submit_sets_flag_and_creates_notifications(self):
        # login as teacher and submit final grade
        self.client.force_login(self.teacher)
        url = reverse('enter_grades') + f'?subject_id={self.subject.id}&academic_year=2024-2025&semester=first'
        post_data = {
            f'grade_{self.student.id}': '85',
            'final_submit': '1'
        }
        resp = self.client.post(url, post_data, follow=True)
        # grade should exist and be finalized
        grade = Grade.objects.filter(subject=self.subject, student=self.student).first()
        self.assertIsNotNone(grade, 'Grade record not created')
        self.assertTrue(grade.is_finalized, 'Grade not marked finalized')
        self.assertIsNotNone(grade.finalized_at, 'finalized_at not set')

        # notifications for student and parent created
        student_notif = Notification.objects.filter(user=self.student, title__icontains='Final Grade Submitted').exists()
        parent_notif = Notification.objects.filter(user=self.parent, title__icontains='Child Result Submitted').exists()
        self.assertTrue(student_notif, 'Student notification missing')
        self.assertTrue(parent_notif, 'Parent notification missing')

    def test_registrar_dashboard_shows_recent_final_submissions(self):
        # create a finalized grade
        g = Grade.objects.create(student=self.student, subject=self.subject, score=90, is_finalized=True, finalized_at=timezone.now())
        # create registrar user
        registrar = User.objects.create_user(username='reg1', email='r1@example.com', password='pass')
        registrar.role = 'registrar'
        registrar.is_approved = True
        registrar.save()
        self.client.force_login(registrar)
        url = reverse('registrar_dashboard')
        resp = self.client.get(url)
        # view should include recent_final_submissions in context
        self.assertIn('recent_final_submissions', resp.context)
        self.assertTrue(resp.context['recent_final_submissions'].count() >= 1)
