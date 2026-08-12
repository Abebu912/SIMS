from django.db import migrations


def set_initial_balance(apps, schema_editor):
    StudentProfile = apps.get_model('users', 'StudentProfile')
    from decimal import Decimal
    # Set balance to 5000.00 for any existing student with zero or negative balance
    StudentProfile.objects.filter(balance__lte=0).update(balance=Decimal('5000.00'))


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_studentprofile_balance'),
    ]

    operations = [
        migrations.RunPython(set_initial_balance, migrations.RunPython.noop),
    ]
