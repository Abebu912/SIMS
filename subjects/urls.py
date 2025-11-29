# subjects/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SubjectViewSet, EnrollmentViewSet  # Changed CourseViewSet to SubjectViewSet

router = DefaultRouter()
router.register(r"", SubjectViewSet)  # Changed to SubjectViewSet
router.register(r"enrollments", EnrollmentViewSet)

urlpatterns = [
    path("", include(router.urls)),
]