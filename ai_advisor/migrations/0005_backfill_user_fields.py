from django.db import migrations


def forwards(apps, schema_editor):
    User = apps.get_model('users', 'User')
    AIConversation = apps.get_model('ai_advisor', 'AIConversation')
    AIAssistantLog = apps.get_model('ai_advisor', 'AIAssistantLog')
    LearningPlan = apps.get_model('ai_advisor', 'LearningPlan')
    ActivitySuggestion = apps.get_model('ai_advisor', 'ActivitySuggestion')
    StudentPreference = apps.get_model('ai_advisor', 'StudentPreference')

    admin = User.objects.filter(is_superuser=True).first()
    if not admin:
        admin = User.objects.first()
    if not admin:
        # nothing we can do
        return

    # Backfill NULL user/student fields to admin for legacy rows
    try:
        AIConversation.objects.filter(user__isnull=True).update(user=admin)
    except Exception:
        pass

    try:
        AIAssistantLog.objects.filter(user__isnull=True).update(user=admin)
    except Exception:
        pass

    try:
        LearningPlan.objects.filter(student__isnull=True).update(student=admin)
    except Exception:
        pass

    try:
        ActivitySuggestion.objects.filter(student__isnull=True).update(student=admin)
    except Exception:
        pass

    try:
        StudentPreference.objects.filter(user__isnull=True).update(user=admin)
    except Exception:
        pass


def reverse(apps, schema_editor):
    # Irreversible safe operation: do not remove assignments automatically
    return


class Migration(migrations.Migration):

    dependencies = [
        ('ai_advisor', '0004_initial'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(forwards, reverse),
    ]
