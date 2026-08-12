# In your urls.py
from django.urls import path
from . import views

urlpatterns = [
    # API endpoints
    path('api/students/announcements/', views.student_announcements_api, name='student_announcements_api'),
    path('api/announcements/', views.student_announcements_api, name='student_announcements_api'),

    # Web pages / admin helpers used by sidebar links
    # Use distinct names for placeholder routes to avoid name collisions
    path('post-announcement/', views.post_announcements, name='notifications_post_announcements'),
    path('manage-users/', views.manage_users, name='notifications_manage_users'),
    path('add-user/', views.add_user, name='notifications_add_user'),
    path('system-settings/', views.system_settings, name='notifications_system_settings'),
    path('generate-reports/', views.generate_reports, name='notifications_generate_reports'),
]