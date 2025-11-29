#!/usr/bin/env python3
"""Check update-grade page for a valid enrollment (taught by a teacher) using Django test client."""
import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sims.settings')
sys.path.insert(0, os.path.abspath('.'))
import django
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from subjects.models import Enrollment

User = get_user_model()

teacher = User.objects.filter(role='teacher').first() or User.objects.filter(is_superuser=True).first() or User.objects.first()
print('Using teacher:', getattr(teacher, 'username', None))
client = Client()
if teacher:
    client.force_login(teacher)

# find an enrollment where subject.instructor is this teacher
enr = Enrollment.objects.select_related('subject', 'student').filter(subject__instructor__user=teacher).first()
if not enr:
    print('No enrollment found for subjects taught by this teacher; trying any enrollment')
    enr = Enrollment.objects.select_related('subject', 'student').first()

if not enr:
    print('No enrollment records found; aborting')
    sys.exit(1)

print('Testing enrollment id:', enr.id, 'subject:', enr.subject.id)
resp = client.get(f'/teachers/update-grade/{enr.id}/', SERVER_NAME='127.0.0.1', SERVER_PORT='8000')
print('Status', resp.status_code)
if resp.status_code == 200:
    print('Page loaded OK (length)', len(resp.content))
else:
    print('Response content:', resp.content)
