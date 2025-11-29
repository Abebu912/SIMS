#!/usr/bin/env python3
"""Check teacher pages using Django test client.

Run: python tools/check_teacher_pages.py

This logs the HTTP status and response size for each URL and prints tracebacks
if an exception occurs while fetching a page.
"""
import os
import sys
from pathlib import Path

# Ensure project root is on sys.path so `sims` package can be imported
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sims.settings')
import django
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model


def pick_user():
    User = get_user_model()
    # Prefer a teacher role, fallback to superuser, then any user
    teacher = None
    try:
        teacher = User.objects.filter(role='teacher').first()
    except Exception:
        teacher = None
    if not teacher:
        try:
            teacher = User.objects.filter(is_superuser=True).first()
        except Exception:
            teacher = None
    if not teacher:
        try:
            teacher = User.objects.first()
        except Exception:
            teacher = None
    return teacher


def main():
    user = pick_user()
    print('Using user:', getattr(user, 'username', None))

    client = Client()
    if user:
        client.force_login(user)

    urls = [
        '/',
        '/teachers/dashboard/',
        '/teachers/enter-grades/',
        '/teachers/bulk-score-upload/1/',
    ]

    for u in urls:
        try:
            # Set host so Django doesn't reject the test client request
            r = client.get(u, SERVER_NAME='127.0.0.1', SERVER_PORT='8000')
            print(f"{u} -> {r.status_code} (size={len(r.content)})")
        except Exception as e:
            import traceback
            print(f"{u} -> ERROR: {e}")
            traceback.print_exc()


if __name__ == '__main__':
    main()
