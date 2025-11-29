# students/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Template URLs only
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    path('subject-registration/', views.subject_registration, name='subject_registration'),
    path('transcripts/', views.view_transcripts, name='view_transcripts'),
    path('transcripts/download-pdf/', views.download_transcript_pdf, name='download_transcript_pdf'),
    path('pay-fees/', views.pay_fees, name='pay_fees'),
    path('ai-advisor/', views.interact_with_ai, name='interact_with_ai'),
    path('announcements/', views.view_announcements, name='view_announcements'),
    # AJAX endpoints
    path('api/notifications/', views.get_notifications_ajax, name='get_notifications_ajax'),
    path('api/announcements/', views.get_announcements_ajax, name='get_announcements_ajax'),
]