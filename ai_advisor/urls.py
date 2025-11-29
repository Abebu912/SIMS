from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AIConversationViewSet, SubjectRecommendationViewSet

router = DefaultRouter()
router = DefaultRouter()
router.register(r'ai-conversations', AIConversationViewSet, basename='ai-conversations')
router.register(r'subject-recommendations', SubjectRecommendationViewSet, basename='subject-recommendations')
urlpatterns = [
    path("", include(router.urls)),
]
