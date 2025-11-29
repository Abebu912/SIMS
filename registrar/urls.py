from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.registrar_dashboard, name='registrar_dashboard'),
    path('assign-subjects/', views.assign_subjects_to_teacher, name='assign_subjects_to_teacher'),
    path('unassign-subject/<int:subject_id>/', views.unassign_subject_from_teacher, name='unassign_subject_from_teacher'),
    path('unassign-subjects-by-teacher/', views.unassign_subject_from_teacher, name='unassign_subjects_by_teacher'),
    path('approve-registrations/', views.approve_registrations, name='approve_registrations'),
    path('academic-records/', views.manage_academic_records, name='manage_academic_records'),
    path('waitlist/<int:subject_id>/', views.handle_waitlist, name='handle_waitlist'),
    path('generate-transcripts/', views.generate_transcripts, name='generate_transcripts'),
]