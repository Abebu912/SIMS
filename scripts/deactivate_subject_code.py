"""
Deactivate subject records by code across all grades.
Usage: python deactivate_subject_code.py CODE
Example: python deactivate_subject_code.py MATH-G1

This script inserts the project root into sys.path, sets DJANGO_SETTINGS_MODULE,
and calls django.setup() before performing ORM operations.
"""
import os
import sys
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sims.settings')

import django
django.setup()

from subjects.models import Subject
import argparse

parser = argparse.ArgumentParser(description='Deactivate subjects by code')
parser.add_argument('code', help='Subject code to deactivate (e.g., MATH-G1)')
args = parser.parse_args()

code = args.code.strip()

qs = Subject.objects.filter(code=code, is_active=True)
count = qs.count()
if count == 0:
    print(f'No active subjects found with code "{code}".')
else:
    qs.update(is_active=False)
    print(f'Deactivated {count} subject(s) with code "{code}".')

# Print affected records for verification
affected = Subject.objects.filter(code=code)
for s in affected:
    print(f'- {s} | is_active={s.is_active} | grade={s.grade_level}')
