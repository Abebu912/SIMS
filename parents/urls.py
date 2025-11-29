from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.parent_dashboard, name='parent_dashboard'),
    path('children/', views.view_children, name='view_children'),
    path('quick-actions/fees/', views.parent_fees_summary, name='parent_fees_summary'),
    path('quick-actions/progress/', views.parent_progress_overview, name='parent_progress_overview'),
    path('quick-actions/contact/', views.parent_contact_teachers_overview, name='parent_contact_teachers_overview'),
    path('request-link/', views.request_child_link, name='request_child_link'),
    path('teacher/<int:teacher_id>/message/', views.message_teacher, name='message_teacher'),
    path('child/<int:student_id>/ranks/', views.child_ranks, name='child_ranks'),
    path('child/<int:student_id>/attendance/', views.child_attendance, name='child_attendance'),
    path('child/<int:student_id>/schedule/', views.child_schedule, name='child_schedule'),
    path('child/<int:student_id>/fees/', views.child_fees, name='child_fees'),
    path('child/<int:student_id>/teachers/', views.contact_teachers, name='contact_teachers'),
    path('child/<int:student_id>/meeting/<int:teacher_id>/', views.request_meeting, name='request_meeting'),
    path('announcements/', views.school_announcements, name='school_announcements'),
]