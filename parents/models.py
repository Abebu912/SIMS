from django.db import models
from django.conf import settings


class ChildLinkRequest(models.Model):
    parent = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    child_identifier = models.CharField(max_length=255)
    relationship = models.CharField(max_length=100, blank=True, null=True)
    message = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Link request by {self.parent} for {self.child_identifier} ({self.status})"


class MeetingRequest(models.Model):
    parent = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='meeting_requests')
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE)
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='meeting_requests_received')
    meeting_date = models.CharField(max_length=64, blank=True, null=True)
    meeting_time = models.CharField(max_length=64, blank=True, null=True)
    purpose = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"MeetingRequest(parent={self.parent}, student={self.student}, teacher={self.teacher}, status={self.status})"
