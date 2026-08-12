from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_alter_studentprofile_balance'),
    ]

    operations = [
        migrations.CreateModel(
            name='StudentStatusLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[('promoted', 'Promoted'), ('failed', 'Failed/Repeat')], max_length=20)),
                ('academic_year', models.CharField(blank=True, max_length=9)),
                ('previous_grade', models.PositiveSmallIntegerField(null=True, blank=True)),
                ('new_grade', models.PositiveSmallIntegerField(null=True, blank=True)),
                ('note', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('performed_by', models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name='performed_status_actions', to='users.user')),
                ('student', models.ForeignKey(on_delete=models.CASCADE, related_name='status_logs', to='users.user', limit_choices_to={'role': 'student'})),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
