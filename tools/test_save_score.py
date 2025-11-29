#!/usr/bin/env python3
"""Test the `save_student_score` endpoint using Django test client.

Run from project root with: python tools\test_save_score.py
"""
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sims.settings')
sys.path.insert(0, os.path.abspath('.'))
import django
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from subjects.models import Subject, Enrollment

User = get_user_model()

def pick_teacher():
    return User.objects.filter(role='teacher').first() or User.objects.filter(is_superuser=True).first() or User.objects.first()

def main():
    teacher = pick_teacher()
    print('Using user:', getattr(teacher, 'username', None))
    client = Client()
    if teacher:
        client.force_login(teacher)

    # Prefer an enrollment for a subject taught by this teacher
    enrollment = None
    if teacher:
        enrollment = Enrollment.objects.select_related('subject', 'student').filter(subject__instructor__user=teacher, status__in=['approved','active']).first()
    if not enrollment:
        # fallback to any approved/active enrollment
        enrollment = Enrollment.objects.select_related('subject', 'student').filter(status__in=['approved','active']).first()
    if not enrollment:
        print('No enrollment records found; aborting test.')
        return
    subject = enrollment.subject
    student = enrollment.student
    print('Using enrollment:', enrollment.id)
    print('Student id:', student.id)

    url = reverse('save_student_score')
    resp = client.post(url, {'student_id': student.id, 'subject_id': subject.id, 'score': '91', 'result': 'Good work'}, SERVER_NAME='127.0.0.1', SERVER_PORT='8000')
    print('Status code:', resp.status_code)
    try:
        print('Response:', resp.json())
    except Exception:
        print('Response content:', resp.content)

if __name__ == '__main__':
    main()
