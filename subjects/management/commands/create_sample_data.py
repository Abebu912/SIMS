# subjects/management/commands/create_sample_data.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from subjects.models import Teacher, Subject

User = get_user_model()
import random

class Command(BaseCommand):
    help = 'Create sample teachers and subjects with schedules'
    
    def handle(self, *args, **options):
        # Create sample teachers
        teachers_data = [
            {'first_name': 'John', 'last_name': 'Smith', 'teacher_id': 'T001', 'department': 'Mathematics'},
            {'first_name': 'Sarah', 'last_name': 'Johnson', 'teacher_id': 'T002', 'department': 'Science'},
            {'first_name': 'Michael', 'last_name': 'Brown', 'teacher_id': 'T003', 'department': 'English'},
            {'first_name': 'Emily', 'last_name': 'Davis', 'teacher_id': 'T004', 'department': 'History'},
            {'first_name': 'David', 'last_name': 'Wilson', 'teacher_id': 'T005', 'department': 'Arts'},
        ]
        
        teachers = []
        for teacher_data in teachers_data:
            user, created = User.objects.get_or_create(
                username=teacher_data['teacher_id'].lower(),
                defaults={
                    'first_name': teacher_data['first_name'],
                    'last_name': teacher_data['last_name'],
                    'email': f"{teacher_data['teacher_id'].lower()}@school.edu",
                }
            )
            if created:
                user.set_password('password123')
                user.save()
            
            teacher, created = Teacher.objects.get_or_create(
                user=user,
                defaults={
                    'teacher_id': teacher_data['teacher_id'],
                    'department': teacher_data['department'],
                }
            )
            teachers.append(teacher)
            self.stdout.write(f"Created teacher: {teacher}")
        
        # Create sample subjects for Grade 1 with schedules
        subjects_data = [
            # Core subjects
            {'code': 'MATH101', 'name': 'Mathematics Fundamentals', 'credit_hours': 4, 'type': 'core', 
             'day': 'mon', 'start_time': '08:00', 'end_time': '09:30', 'room': 'Room 101'},
            {'code': 'ENG101', 'name': 'English Language', 'credit_hours': 3, 'type': 'core',
             'day': 'tue', 'start_time': '08:00', 'end_time': '09:30', 'room': 'Room 102'},
            {'code': 'SCI101', 'name': 'Basic Science', 'credit_hours': 4, 'type': 'core',
             'day': 'wed', 'start_time': '10:00', 'end_time': '11:30', 'room': 'Lab 201'},
            {'code': 'HIS101', 'name': 'World History', 'credit_hours': 3, 'type': 'core',
             'day': 'thu', 'start_time': '08:00', 'end_time': '09:30', 'room': 'Room 103'},
            
            # Elective subjects
            {'code': 'ART101', 'name': 'Art and Craft', 'credit_hours': 2, 'type': 'elective',
             'day': 'fri', 'start_time': '13:00', 'end_time': '14:30', 'room': 'Art Room'},
            {'code': 'MUS101', 'name': 'Music', 'credit_hours': 2, 'type': 'elective',
             'day': 'mon', 'start_time': '13:00', 'end_time': '14:30', 'room': 'Music Room'},
            {'code': 'PE101', 'name': 'Physical Education', 'credit_hours': 2, 'type': 'elective',
             'day': 'wed', 'start_time': '14:00', 'end_time': '15:30', 'room': 'Playground'},
            {'code': 'COMP101', 'name': 'Computer Basics', 'credit_hours': 3, 'type': 'elective',
             'day': 'tue', 'start_time': '10:00', 'end_time': '11:30', 'room': 'Computer Lab'},
        ]
        
        for i, subject_data in enumerate(subjects_data):
            subject, created = Subject.objects.get_or_create(
                code=subject_data['code'],
                defaults={
                    'name': subject_data['name'],
                    'credit_hours': subject_data['credit_hours'],
                    'subject_type': subject_data['type'],
                    'grade_level': 1,
                    'day_of_week': subject_data['day'],
                    'start_time': subject_data['start_time'],
                    'end_time': subject_data['end_time'],
                    'room': subject_data['room'],
                    'instructor': teachers[i % len(teachers)],  # Assign teachers round-robin
                    'max_capacity': 30,
                    'is_active': True,
                }
            )
            if created:
                self.stdout.write(f"Created subject: {subject}")
            else:
                self.stdout.write(f"Subject already exists: {subject}")
        
        self.stdout.write(self.style.SUCCESS('Successfully created sample data!'))