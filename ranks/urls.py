from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GradeViewSet, TranscriptViewSet

router = DefaultRouter()
router.register(r"", GradeViewSet)
router.register(r"transcripts", TranscriptViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
