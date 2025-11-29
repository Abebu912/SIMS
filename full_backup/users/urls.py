from django.urls import path
from . import views, admin_views

urlpatterns = [
    # Admin URLs
    path('admin-panel/', admin_views.admin_panel, name='admin_panel'),
    path('manage-users/', admin_views.manage_users, name='manage_users'),
    path('add-user/', admin_views.add_user, name='add_user'),
    path('system-settings/', admin_views.system_settings, name='system_settings'),
    path('generate-reports/', admin_views.generate_reports, name='generate_reports'),
    path('post-announcement/', admin_views.post_announcement, name='post_announcement'),
]