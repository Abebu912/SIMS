# subjects/admin.py
from django.contrib import admin
from .models import Subject, Enrollment

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'grade_level', 'is_active', 'max_capacity', 'created_at']
    list_filter = ['is_active', 'grade_level', 'created_at']
    search_fields = ['name', 'code', 'description']
    list_editable = ['is_active', 'max_capacity']
    ordering = ['grade_level', 'name']

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'subject', 'academic_year', 'enrolled_date', 'status']
    list_filter = ['status', 'academic_year', 'enrolled_date']
    search_fields = ['student__username', 'subject__name', 'academic_year']
    date_hierarchy = 'enrolled_date'