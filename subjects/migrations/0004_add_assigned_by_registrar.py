from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subjects', '0003_add_result'),
    ]

    operations = [
        migrations.AddField(
            model_name='subject',
            name='assigned_by_registrar',
            field=models.BooleanField(default=False),
        ),
    ]
