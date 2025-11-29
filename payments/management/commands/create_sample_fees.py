# payments/management/commands/create_sample_fees.py
from django.core.management.base import BaseCommand
from payments.models import FeeStructure
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Create sample fee structures'
    
    def handle(self, *args, **options):
        # Use Django's get_user_model() to get the correct User model
        User = get_user_model()
        
        # Get or create a superuser for created_by field
        try:
            user = User.objects.filter(is_superuser=True).first()
            if not user:
                # Create a superuser if none exists
                user = User.objects.create_superuser(
                    username='admin',
                    email='admin@example.com',
                    password='admin123'
                )
                self.stdout.write(self.style.SUCCESS('Created superuser: admin'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Using superuser: {user.username}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error getting user: {e}'))
            return
        
        fees = [
            {"name": "Tuition Fee", "amount": 1000.00, "description": "Annual tuition fee"},
            {"name": "Library Fee", "amount": 50.00, "description": "Library access fee"},
            {"name": "Lab Fee", "amount": 75.00, "description": "Science laboratory fee"},
            {"name": "Sports Fee", "amount": 25.00, "description": "Sports facility fee"},
            {"name": "Exam Fee", "amount": 30.00, "description": "Examination fee"},
        ]
        
        created_count = 0
        for fee_data in fees:
            try:
                # Check if fee already exists
                existing_fee = FeeStructure.objects.filter(name=fee_data["name"]).first()
                
                if existing_fee:
                    self.stdout.write(
                        self.style.WARNING(f'Already exists: {existing_fee.name} - ${existing_fee.amount}')
                    )
                else:
                    # Create new fee with created_by
                    fee = FeeStructure.objects.create(
                        name=fee_data["name"],
                        amount=fee_data["amount"],
                        description=fee_data["description"],
                        is_active=True,
                        created_by=user
                    )
                    self.stdout.write(
                        self.style.SUCCESS(f'Created: {fee.name} - ${fee.amount}')
                    )
                    created_count += 1
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error creating {fee_data["name"]}: {e}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} fee structures')
        )