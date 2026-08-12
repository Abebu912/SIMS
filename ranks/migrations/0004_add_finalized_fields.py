from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ranks', '0003_grade_assignment_score_grade_final_exam_score_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='grade',
            name='is_finalized',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='grade',
            name='finalized_at',
            field=models.DateTimeField(null=True, blank=True),
        ),
    ]
