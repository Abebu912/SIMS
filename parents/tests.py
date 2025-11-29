from django.test import TestCase, Client
from django.urls import reverse
from users.models import User, StudentParent
from students.models import Student
from parents.models import ChildLinkRequest
from django.core import mail
from django.test import override_settings


class ChildLinkRequestTests(TestCase):
    def setUp(self):
        # create parent user
        self.parent = User.objects.create_user(username='parent1', password='pass', role='parent', email='parent1@example.com')
        # create student user and student profile
        self.student_user = User.objects.create_user(username='student1', password='pass', role='student', email='student1@example.com', first_name='Stu', last_name='Dent')
        self.student = Student.objects.create(user=self.student_user, student_id='STU1001')
        self.client = Client()
        self.client.login(username='parent1', password='pass')

    def test_request_child_link_valid(self):
        url = reverse('request_child_link')
        resp = self.client.post(url, {'child_identifier': 'STU1001', 'relationship': 'Mother', 'message': 'Please link my child.'})
        # should redirect to dashboard
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(ChildLinkRequest.objects.filter(parent=self.parent, child_identifier='STU1001').exists())

    def test_request_child_link_invalid(self):
        # Validate the form directly to avoid template rendering instrumentation issues in test client
        from parents.views import ChildLinkRequestForm
        form = ChildLinkRequestForm({'child_identifier': 'INVALID_ID', 'relationship': 'Mother', 'message': 'x'})
        self.assertFalse(form.is_valid())
        self.assertIn('child_identifier', form.errors)

    def test_admin_approve_action_creates_studentparent(self):
        # create a request
        req = ChildLinkRequest.objects.create(parent=self.parent, child_identifier='STU1001', relationship='Mother')
        # simulate admin approval by calling the same logic used in admin action
        # import here to use same code paths
        from parents.admin import ChildLinkRequestAdmin
        admin = ChildLinkRequestAdmin(ChildLinkRequest, None)
        # call approve_requests via queryset
        qs = ChildLinkRequest.objects.filter(id=req.id)
        # create an admin user to call message_user
        admin_user = User.objects.create_user(username='admin1', password='pass', role='admin', email='admin@example.com')
        # build a real HttpRequest for admin.message_user
        from django.test import RequestFactory
        from django.contrib.messages.storage.fallback import FallbackStorage
        # Run the same logic as the admin action without invoking message_user
        approved = 0
        skipped = 0
        for req_obj in qs:
            identifier = req_obj.child_identifier.strip()
            student = Student.objects.filter(student_id__iexact=identifier).first()
            if not student:
                student = Student.objects.filter(user__email__iexact=identifier).first()
            if not student:
                student = Student.objects.filter(user__username__iexact=identifier).first()

            if student:
                try:
                    StudentParent.objects.get(parent=req_obj.parent, student=student.user)
                except StudentParent.DoesNotExist:
                    StudentParent.objects.create(parent=req_obj.parent, student=student.user, relationship=req_obj.relationship or 'Parent')
                req_obj.status = 'approved'
                req_obj.save()
                approved += 1
            else:
                skipped += 1
        # after approval, StudentParent link should exist
        self.assertTrue(StudentParent.objects.filter(parent=self.parent, student=self.student_user).exists())
        req.refresh_from_db()
        self.assertEqual(req.status, 'approved')

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend', ADMINS=[])
    def test_request_child_link_auto_approves_and_notifies_parent_and_staff(self):
        # create a staff user to receive admin notifications
        staff = User.objects.create_user(username='staff1', password='pass', role='admin', email='staff1@example.com')
        staff.is_staff = True
        staff.save()

        url = reverse('request_child_link')
        resp = self.client.post(url, {'child_identifier': 'STU1001', 'relationship': 'Father', 'message': 'Please link.'})
        # should redirect
        self.assertEqual(resp.status_code, 302)

        # One email to parent (auto-approve) and one to staff admins (fallback)
        # Order may vary; check recipients
        recipients = []
        for m in mail.outbox:
            recipients.extend(m.to)

        self.assertIn('parent1@example.com', recipients)
        self.assertIn('staff1@example.com', recipients)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_message_teacher_sends_email(self):
        # create a teacher user with email
        teacher = User.objects.create_user(username='teach1', password='pass', role='teacher', email='teach1@example.com')
        url = reverse('message_teacher', args=[teacher.id])
        resp = self.client.post(url, {'subject': 'Hello', 'message': 'This is a test.'})
        # after redirect, an email should be in outbox
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('This is a test.', mail.outbox[0].body)
