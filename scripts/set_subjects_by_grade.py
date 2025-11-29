#!/usr/bin/env python
import os
import sys
from pathlib import Path

# Ensure project root is on sys.path so the `sims` package can be imported
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

# Point to the Django settings module for this project
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sims.settings')

import django
django.setup()

from subjects.models import Subject
from django.db import transaction

# Subjects mapping based on user's hint
GRADE_SUBJECTS = {
    1: [
        'Amharic',
        'English',
        'Environmental Science',
        'Moral Education',
        'Performing and Visual Arts',
        'Health and Physical Education',
    ],
    2: [
        'Amharic',
        'English',
        'Environmental Science',
        'Moral Education',
        'Performing and Visual Arts',
        'Health and Physical Education',
    ],
    3: [
        'Amharic',
        'English',
        'Environmental Science',
        'Moral Education',
        'Performing and Visual Arts',
        'Health and Physical Education',
    ],
    4: [
        'Amharic',
        'English',
        'Environmental Science',
        'Moral Education',
        'Performing and Visual Arts',
        'Health and Physical Education',
    ],
    5: [
        'Amharic',
        'English',
        'Environmental Science',
        'Moral Education',
        'Performing and Visual Arts',
        'Health and Physical Education',
    ],
    6: [
        'Amharic',
        'English',
        'Environmental Science',
        'Moral Education',
        'Performing and Visual Arts',
        'Health and Physical Education',
    ],
    # Grades 7 and 8: user provided list -> expanded to 11 by including Moral Education as well
    7: [
        'Amharic',
        'English',
        'Mathematics',
        'General Science',
        'Social Studies',
        'Citizenship Education',
        'Performing and Visual Arts',
        'Information Technology',
        'Health and Physical Education',
        'Career and Technical Education',
    ],
    8: [
        'Amharic',
        'English',
        'Mathematics',
        'General Science',
        'Social Studies',
        'Citizenship Education',
        'Performing and Visual Arts',
        'Information Technology',
        'Health and Physical Education',
        'Career and Technical Education',
    ],
}

# Subjects to remove/deactivate per user's request (grade -> list of subject names)
GRADE_SUBJECTS_TO_REMOVE = {
    2: ['Science', 'Social Studies'],
    3: ['Science', 'Social Studies'],
    4: ['Science', 'Geography'],
    5: ['Science', 'Biology'],
    6: ['Science', 'Physics'],
    7: ['Science', 'Chemistry', 'Moral Education'],
    8: ['Advanced Science', 'Science', 'Moral Education'],
}


def slug_to_code(grade, name):
    # Generate a simple code: G{grade}_{SHORT}
    short = ''.join([c for c in name.upper() if c.isalpha()])
    short = short.replace('AND', '')[:6]
    return f'G{grade}_{short}'


def ensure_subject(grade, name):
    code = slug_to_code(grade, name)
    with transaction.atomic():
        subject, created = Subject.objects.get_or_create(
            name=name,
            grade_level=grade,
            defaults={
                'code': code,
                'description': f'{name} for Grade {grade}',
                'credit_hours': 3,
                'subject_type': 'core',
                'is_active': True,
            }
        )
        # If exists, update properties to match expected core/defaults
        updated = False
        if subject.code != code:
            # avoid collision: ensure unique by appending id if needed
            subject.code = code
            updated = True
        if subject.subject_type != 'core':
            subject.subject_type = 'core'
            updated = True
        if not subject.is_active:
            subject.is_active = True
            updated = True
        if updated:
            subject.save()
    return subject, created


def run():
    print('Setting up subjects for grades 1-8...')
    created_total = 0
    updated_total = 0
    for grade, names in GRADE_SUBJECTS.items():
        print(f'\nGrade {grade}:')
        for name in names:
            subj, created = ensure_subject(grade, name)
            if created:
                print(f'  Created: {subj.name} (code={subj.code})')
                created_total += 1
            else:
                print(f'  Exists/Updated: {subj.name} (code={subj.code})')
                updated_total += 1

        # Deactivate/remove any specified subjects for this grade
        remove_list = GRADE_SUBJECTS_TO_REMOVE.get(grade, [])
        if remove_list:
            for rem in remove_list:
                matches = Subject.objects.filter(grade_level=grade, name__iexact=rem)
                for m in matches:
                    if m.is_active:
                        m.is_active = False
                        m.save()
                        print(f'  Deactivated: {m.name} (grade={grade})')

    print(f'\nDone. Created: {created_total}, Updated: {updated_total}')


if __name__ == '__main__':
    run()
