from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_add_finance_balance'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentprofile',
            name='is_repeating',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='studentprofile',
            name='repeated_years',
            field=models.PositiveSmallIntegerField(default=0),
        ),
    ]
