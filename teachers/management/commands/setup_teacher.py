from django.core.management.base import BaseCommand
from subjects.models import Subject, Teacher, Enrollment
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Setup teacher with subjects and enrollments'
    
    def handle(self, *args, **options):
        # Get or create teacher
        teacher_user, created = User.objects.get_or_create(
            username='melese',
            defaults={
                'first_name': 'Melese',
                'last_name': 'Alemante',
                'email': 'melese@school.edu',
                'role': 'teacher'
            }
        )
        
        teacher, teacher_created = Teacher.objects.get_or_create(
            user=teacher_user,
            defaults={
                'teacher_id': 'T001',
                'department': 'Elementary Education',
                'office_location': 'Room 101'
            }
        )
        
        # Create or assign subjects
        subjects_data = [
            {'name': 'Mathematics', 'code': 'MATH-G1', 'grade_level': 1},
            {'name': 'English Reading', 'code': 'ENG-G1', 'grade_level': 1},
            {'name': 'Science', 'code': 'SCI-G1', 'grade_level': 1},
            {'name': 'Art', 'code': 'ART-G1', 'grade_level': 1},
        ]
        
        for sub_data in subjects_data:
            subject, created = Subject.objects.get_or_create(
                code=sub_data['code'],
                defaults={
                    'name': sub_data['name'],
                    'grade_level': sub_data['grade_level'],
                    'instructor': teacher,
                    'description': f"{sub_data['name']} for Grade 1",
                    'is_active': True
                }
            )
            if not created:
                subject.instructor = teacher
                subject.is_active = True
                subject.save()
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully setup teacher {teacher_user.username} with subjects!')
        )