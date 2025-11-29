# In your urls.py
from django.urls import path
from .views import student_announcements_api

urlpatterns = [
    path('api/students/announcements/', student_announcements_api, name='student_announcements_api'),
    path('api/announcements/', student_announcements_api, name='student_announcements_api'),
]