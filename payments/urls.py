from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FeeStructureViewSet, PaymentViewSet

router = DefaultRouter()
router.register(r"fees", FeeStructureViewSet)
router.register(r"", PaymentViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
