from django.db import models
from users.models import User
from subjects.models import Subject

class AIConversation(models.Model):
    """Model to store AI conversation sessions for elementary students"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    conversation_type = models.CharField(max_length=50, choices=[
        ('homework_help', 'Homework Help'),
        ('subject_help', 'Subject Help'),
        ('study_help', 'Study Help'),
        ('general', 'General Question')
    ], default='general')
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"AI Chat: {self.user.username} - {self.title or 'No Title'}"
    
    def save(self, *args, **kwargs):
        if not self.title:
            from django.utils import timezone
            self.title = f"Chat {timezone.now().strftime('%Y-%m-%d %H:%M')}"
        super().save(*args, **kwargs)

class AIMessage(models.Model):
    """Model to store individual messages in AI conversations"""
    conversation = models.ForeignKey(AIConversation, on_delete=models.CASCADE, related_name='messages')
    content = models.TextField()
    is_user = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    message_type = models.CharField(max_length=50, choices=[
        ('text', 'Text'),
        ('question', 'Question'),
        ('suggestion', 'Suggestion'),
        ('help', 'Help')
    ], default='text')
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        role = "Student" if self.is_user else "Helper"
        return f"{role}: {self.content[:50]}..."

class SubjectRecommendation(models.Model):
    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name="subject_recommendations"
    )
    subject = models.ForeignKey(
        'subjects.Subject',
        on_delete=models.CASCADE,
        related_name="recommendations"
    )
    confidence_score = models.FloatField(default=0.0)
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-confidence_score']
    
    def __str__(self):
        return f"{self.student.user.username} - {self.subject.name} ({self.confidence_score})"

class AIAssistantLog(models.Model):
    """Model to log AI helper interactions"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    action = models.CharField(max_length=100)
    input_data = models.JSONField(default=dict)
    output_data = models.JSONField(default=dict)
    response_time = models.DecimalField(max_digits=6, decimal_places=3, help_text="Response time in seconds")
    created_at = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        status = "Success" if self.success else "Failed"
        return f"Helper Log: {self.user.username} - {self.action} - {status}"

class LearningPlan(models.Model):
    """Model to store AI-generated learning plans for elementary students"""
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'student'}, null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    weekly_plan = models.JSONField(default=dict)  # Store week-wise learning activities
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Learning Plan: {self.student.username} - {self.title}"

class ActivitySuggestion(models.Model):
    """Model to store AI-generated learning activity suggestions"""
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'student'}, null=True, blank=True)
    activity_type = models.CharField(max_length=200)
    description = models.TextField()
    recommended_subjects = models.ManyToManyField(Subject, related_name='activity_suggestions')
    skills_developed = models.JSONField(default=list)
    difficulty_level = models.CharField(max_length=20, choices=[
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard')
    ], default='medium')
    time_required = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Activity: {self.student.username} - {self.activity_type}"

class StudyTip(models.Model):
    """Model to store AI-generated study tips for kids"""
    title = models.CharField(max_length=200)
    content = models.TextField()
    category = models.CharField(max_length=50, choices=[
        ('homework', 'Homework Help'),
        ('reading', 'Reading Tips'),
        ('math', 'Math Help'),
        ('science', 'Science Help'),
        ('general', 'General Study Tips')
    ], default='general')
    grade_level = models.CharField(max_length=20, choices=[
        ('all', 'All Grades'),
        ('1-2', 'Grades 1-2'),
        ('3-4', 'Grades 3-4'),
        ('5-6', 'Grades 5-6'),
        ('7-8', 'Grades 7-8')
    ], default='all')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Study Tip: {self.title}"

class HelperConfiguration(models.Model):
    """Model to store AI helper configuration"""
    name = models.CharField(max_length=100, unique=True)
    api_key = models.CharField(max_length=255, blank=True)
    model_name = models.CharField(max_length=100, default='gpt-3.5-turbo')
    max_tokens = models.IntegerField(default=500)
    temperature = models.DecimalField(max_digits=3, decimal_places=2, default=0.7)
    is_active = models.BooleanField(default=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Helper Config: {self.name}"

class StudentPreference(models.Model):
    """Model to store student preferences for AI helper"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    favorite_subjects = models.JSONField(default=list)
    learning_style = models.CharField(max_length=20, choices=[
        ('visual', 'Visual Learner'),
        ('auditory', 'Auditory Learner'),
        ('kinesthetic', 'Hands-on Learner'),
        ('reading', 'Reading Learner')
    ], default='visual')
    help_preferences = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Preferences: {self.user.username}"