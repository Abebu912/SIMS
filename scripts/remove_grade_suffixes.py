#!/usr/bin/env python
"""
Script to remove trailing "Grade N" suffixes from Subject.name values.
Backs up current subject ids and names to `scripts/subject_names_backup.csv` before modifying.

Run from project root:
    python scripts/remove_grade_suffixes.py

This script configures Django using `sims.settings` (same as `manage.py`).
"""
import os
import re
import csv
import sys
import django

# Ensure project root is on sys.path so Django settings package can be imported
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sims.settings')
try:
    django.setup()
except Exception as e:
    print('Error setting up Django:', e)
    raise

from subjects.models import Subject

BACKUP_PATH = os.path.join(os.path.dirname(__file__), 'subject_names_backup.csv')

pattern = re.compile(r"\s+Grade\s*\d+\s*$", flags=re.IGNORECASE)

subjects = Subject.objects.all()
if not subjects.exists():
    print('No subjects found in the database.')

# Backup
with open(BACKUP_PATH, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['id', 'original_name'])
    for s in subjects:
        writer.writerow([s.id, s.name])

changed = 0
for s in subjects:
    new_name = pattern.sub('', s.name).strip()
    if new_name != s.name:
        print(f'Updating Subject id={s.id}: "{s.name}" -> "{new_name}"')
        s.name = new_name
        try:
            s.save()
            changed += 1
        except Exception as e:
            print(f'Failed to save subject id={s.id}:', e)

print(f'Done. Updated {changed} subjects. Backup written to {BACKUP_PATH}')
