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
