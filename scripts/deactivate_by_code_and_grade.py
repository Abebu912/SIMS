"""
Deactivate specific subject codes for specific grade levels.
This script takes a list of (code, grade) tuples and sets is_active=False
for Subject records that match both fields.

Run from project root:
python .\scripts\deactivate_by_code_and_grade.py

It will print what it changed.
"""
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sims.settings')
import django
django.setup()

from subjects.models import Subject

# Define codes and grades to deactivate
# Format: (code, grade_level)
TO_DEACTIVATE = [
    ('ART-G1', 1),
    ('ART101', 1),
    ('SCI-G1', 1),
    ('SCI101', 1),
    ('ENG-G1', 1),
    ('HIS101', 3),
]

print('Starting deactivation run...')
changed_total = 0
for code, grade in TO_DEACTIVATE:
    qs = Subject.objects.filter(code=code, grade_level=grade, is_active=True)
    n = qs.count()
    if n == 0:
        print(f'No active records found for code={code}, grade={grade}')
        continue
    qs.update(is_active=False)
    changed_total += n
    print(f'Deactivated {n} record(s) for code={code}, grade={grade}')

print(f'Done. Total deactivated: {changed_total}')

# Print current state for those codes
print('\nVerification:')
for code, grade in TO_DEACTIVATE:
    all_q = Subject.objects.filter(code=code, grade_level=grade)
    for s in all_q:
        print(f'- {s.code} | {s.name} | grade={s.grade_level} | is_active={s.is_active} | id={s.id}')
