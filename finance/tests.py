from django.test import TestCase, Client
from django.urls import reverse
from users.models import User
from payments.models import Payment, FeeStructure
from django.test.client import RequestFactory
import finance.views as finance_views


class FinanceViewsTests(TestCase):
    def setUp(self):
        # finance user
        self.finance = User.objects.create_user(username='fin1', password='pass', role='finance', email='fin@example.com')
        # create a student and fee structure and a completed payment
        self.student = User.objects.create_user(username='stu1', password='pass', role='student', email='stu@example.com')
        self.fee = FeeStructure.objects.create(name='Tuition', amount='1000.00', description='Tuition fee', created_by=self.finance)
        self.payment = Payment.objects.create(student=self.student, fee_structure=self.fee, amount_paid='1000.00', payment_method='card', transaction_id='tx1', status='completed')
        self.rf = RequestFactory()

    def test_finance_dashboard_view(self):
        # build a request and attach our finance user
        req = self.rf.get('/finance/dashboard/')
        req.user = self.finance
        resp = finance_views.finance_dashboard(req)
        # view should return an HttpResponse
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode('utf-8')
        self.assertIn('Finance Dashboard', content)
