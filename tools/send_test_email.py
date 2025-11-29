import os, sys
proj = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, proj)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sims.settings')
import django
django.setup()
from django.core.mail import EmailMultiAlternatives
from django.conf import settings

TO = os.environ.get('TEST_EMAIL_TO') or input('Send test email to: ').strip()
SUBJECT = 'Test email from SIMS'
BODY = 'This is a test email sent from the SIMS application. If you received this, SMTP is configured correctly.'
FROM = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@localhost')

msg = EmailMultiAlternatives(SUBJECT, BODY, FROM, [TO])
msg.attach_alternative(f"<html><body><p>{BODY}</p></body></html>", 'text/html')
print('Using EMAIL_BACKEND =', getattr(settings, 'EMAIL_BACKEND', '(not set)'))
print('From:', FROM, 'To:', TO)
try:
    msg.send(fail_silently=False)
    print('Email sent successfully')
except Exception as e:
    print('Failed to send email:', e)
