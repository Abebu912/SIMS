#!/usr/bin/env python3
"""Check parent dashboard using Django test client.

Run: python tools\check_parent_dashboard.py
"""
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sims.settings')
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import django
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model


def pick_parent():
    User = get_user_model()
    try:
        parent = User.objects.filter(role='parent').first()
    except Exception:
        parent = None
    if not parent:
        try:
            parent = User.objects.filter(is_superuser=True).first()
        except Exception:
            parent = None
    if not parent:
        try:
            parent = User.objects.first()
        except Exception:
            parent = None
    return parent


def main():
    user = pick_parent()
    print('Using user:', getattr(user, 'username', None))

    client = Client()
    if user:
        client.force_login(user)

    urls = [
        '/',
        '/dashboard/',
        '/parents/dashboard/',
    ]

    for u in urls:
        try:
            r = client.get(u, SERVER_NAME='127.0.0.1', SERVER_PORT='8000')
            print(f"{u} -> {r.status_code} (size={len(r.content)})")
        except Exception as e:
            import traceback
            print(f"{u} -> ERROR: {e}")
            traceback.print_exc()


if __name__ == '__main__':
    main()
