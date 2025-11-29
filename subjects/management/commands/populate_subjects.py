# subjects/management/commands/populate_subjects.py
from django.core.management.base import BaseCommand
from subjects.models import Subject

class Command(BaseCommand):
    help = 'Populate sample subjects for all grade levels'

    def handle(self, *args, **kwargs):
        subjects_data = [
            # Grade 1 Subjects
            {'name': 'Mathematics Grade 1', 'code': 'MATH101', 'grade_level': 1, 'description': 'Basic mathematics for grade 1', 'max_capacity': 30},
            {'name': 'English Grade 1', 'code': 'ENG101', 'grade_level': 1, 'description': 'English language for grade 1', 'max_capacity': 30},
            {'name': 'Science Grade 1', 'code': 'SCI101', 'grade_level': 1, 'description': 'Basic science for grade 1', 'max_capacity': 25},
            {'name': 'Art Grade 1', 'code': 'ART101', 'grade_level': 1, 'description': 'Art and creativity for grade 1', 'max_capacity': 20},
            
            # Grade 2 Subjects
            {'name': 'Mathematics Grade 2', 'code': 'MATH102', 'grade_level': 2, 'description': 'Mathematics for grade 2', 'max_capacity': 30},
            {'name': 'English Grade 2', 'code': 'ENG102', 'grade_level': 2, 'description': 'English language for grade 2', 'max_capacity': 30},
            {'name': 'Science Grade 2', 'code': 'SCI102', 'grade_level': 2, 'description': 'Science for grade 2', 'max_capacity': 25},
            {'name': 'Social Studies Grade 2', 'code': 'SOC102', 'grade_level': 2, 'description': 'Social studies for grade 2', 'max_capacity': 25},
            
            # Grade 3 Subjects
            {'name': 'Mathematics Grade 3', 'code': 'MATH103', 'grade_level': 3, 'description': 'Mathematics for grade 3', 'max_capacity': 30},
            {'name': 'English Grade 3', 'code': 'ENG103', 'grade_level': 3, 'description': 'English language for grade 3', 'max_capacity': 30},
            {'name': 'Science Grade 3', 'code': 'SCI103', 'grade_level': 3, 'description': 'Science for grade 3', 'max_capacity': 25},
            {'name': 'History Grade 3', 'code': 'HIS103', 'grade_level': 3, 'description': 'History for grade 3', 'max_capacity': 25},
            
            # Grade 4 Subjects
            {'name': 'Mathematics Grade 4', 'code': 'MATH104', 'grade_level': 4, 'description': 'Mathematics for grade 4', 'max_capacity': 30},
            {'name': 'English Grade 4', 'code': 'ENG104', 'grade_level': 4, 'description': 'English language for grade 4', 'max_capacity': 30},
            {'name': 'Science Grade 4', 'code': 'SCI104', 'grade_level': 4, 'description': 'Science for grade 4', 'max_capacity': 25},
            {'name': 'Geography Grade 4', 'code': 'GEO104', 'grade_level': 4, 'description': 'Geography for grade 4', 'max_capacity': 25},
            
            # Grade 5 Subjects
            {'name': 'Mathematics Grade 5', 'code': 'MATH105', 'grade_level': 5, 'description': 'Mathematics for grade 5', 'max_capacity': 30},
            {'name': 'English Grade 5', 'code': 'ENG105', 'grade_level': 5, 'description': 'English language for grade 5', 'max_capacity': 30},
            {'name': 'Science Grade 5', 'code': 'SCI105', 'grade_level': 5, 'description': 'Science for grade 5', 'max_capacity': 25},
            {'name': 'Biology Grade 5', 'code': 'BIO105', 'grade_level': 5, 'description': 'Biology for grade 5', 'max_capacity': 25},
            
            # Grade 6 Subjects
            {'name': 'Mathematics Grade 6', 'code': 'MATH106', 'grade_level': 6, 'description': 'Mathematics for grade 6', 'max_capacity': 30},
            {'name': 'English Grade 6', 'code': 'ENG106', 'grade_level': 6, 'description': 'English language for grade 6', 'max_capacity': 30},
            {'name': 'Science Grade 6', 'code': 'SCI106', 'grade_level': 6, 'description': 'Science for grade 6', 'max_capacity': 25},
            {'name': 'Physics Grade 6', 'code': 'PHY106', 'grade_level': 6, 'description': 'Physics for grade 6', 'max_capacity': 25},
            
            # Grade 7 Subjects
            {'name': 'Mathematics Grade 7', 'code': 'MATH107', 'grade_level': 7, 'description': 'Mathematics for grade 7', 'max_capacity': 30},
            {'name': 'English Grade 7', 'code': 'ENG107', 'grade_level': 7, 'description': 'English language for grade 7', 'max_capacity': 30},
            {'name': 'Science Grade 7', 'code': 'SCI107', 'grade_level': 7, 'description': 'Science for grade 7', 'max_capacity': 25},
            {'name': 'Chemistry Grade 7', 'code': 'CHE107', 'grade_level': 7, 'description': 'Chemistry for grade 7', 'max_capacity': 25},
            
            # Grade 8 Subjects
            {'name': 'Mathematics Grade 8', 'code': 'MATH108', 'grade_level': 8, 'description': 'Mathematics for grade 8', 'max_capacity': 30},
            {'name': 'English Grade 8', 'code': 'ENG108', 'grade_level': 8, 'description': 'English language for grade 8', 'max_capacity': 30},
            {'name': 'Science Grade 8', 'code': 'SCI108', 'grade_level': 8, 'description': 'Science for grade 8', 'max_capacity': 25},
            {'name': 'Advanced Science Grade 8', 'code': 'ASC108', 'grade_level': 8, 'description': 'Advanced science for grade 8', 'max_capacity': 20},
        ]

        created_count = 0
        for subject_data in subjects_data:
            subject, created = Subject.objects.get_or_create(
                code=subject_data['code'],
                defaults=subject_data
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created subject: {subject.name}'))

        self.stdout.write(self.style.SUCCESS(f'Successfully created {created_count} subjects'))
