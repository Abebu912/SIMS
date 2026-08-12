from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_set_initial_balance'),
    ]

    operations = [
        migrations.AddField(
            model_name='financeprofile',
            name='balance',
            field=models.DecimalField(default=0.0, max_digits=12, decimal_places=2),
        ),
    ]
