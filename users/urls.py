from django.urls import path
from . import views, admin_views

urlpatterns = [
    # Admin URLs
    path('manage-users/', admin_views.manage_users, name='manage_users'),
    path('add-user/', admin_views.add_user, name='add_user'),
    path('admin-panel/', admin_views.admin_panel, name='admin_panel'),
    path('manage-users/', admin_views.manage_users, name='manage_users'),
    path('add-user/', admin_views.add_user, name='add_user'),
    path('system-settings/', admin_views.system_settings, name='system_settings'),
    path('generate-reports/', admin_views.generate_reports, name='generate_reports'),
    path('post-announcement/', admin_views.post_announcement, name='post_announcement'),
    path('debug-add-user/', admin_views.debug_add_user, name='debug_add_user'),
    path('students/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('check-schedule-conflicts/', views.check_schedule_conflicts_ajax, name='check_schedule_conflicts'),
    path('subjects/', views.view_subjects, name='view_subjects'),
    path('students/subject-registration/', views.subject_registration, name='subject_registration'),
    path('ranks/', views.view_ranks, name='view_ranks'),
    path('homework/', views.view_homework, name='view_homework'),
    path('ai-assistant/', views.interact_with_ai, name='interact_with_ai'),
    path('announcements/', views.view_announcements, name='view_announcements'),
    path('registrar/dashboard/', views.registrar_dashboard, name='registrar_dashboard'),
path('registrar/approve-registrations/', views.approve_registrations, name='approve_registrations'),
    path('registrar/approve-registration/<int:enrollment_id>/', views.approve_single_registration, name='approve_single_registration'),
    path('registrar/reject-registration/<int:enrollment_id>/', views.reject_single_registration, name='reject_single_registration'),
    path('registrar/bulk-approve/', views.bulk_approve_registrations, name='bulk_approve_registrations'),
    path('registrar/academic-records/', views.manage_academic_records, name='manage_academic_records'),
    path('registrar/student-record/<int:student_id>/', views.student_academic_record, name='student_academic_record'),
    path('registrar/update-grade/<int:enrollment_id>/', views.update_grade, name='update_grade'),
    path('registrar/generate-transcript/<int:student_id>/', views.generate_transcript, name='generate_transcript')
    ,
    path('registrar/student/<int:student_id>/subjects/', views.registrar_student_subjects, name='registrar_student_subjects')
    ]