# Generated manually to add `result` field to Enrollment
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subjects', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='enrollment',
            name='result',
            field=models.CharField(max_length=50, null=True, blank=True, help_text='Result or remark for this enrollment'),
        ),
    ]
