# subjects/views.py
from rest_framework import viewsets
from .models import Subject, Enrollment  # Make sure these models exist
from .serializers import SubjectSerializer, EnrollmentSerializer  # And these serializers

class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer

class EnrollmentViewSet(viewsets.ModelViewSet):
    queryset = Enrollment.objects.all()
    serializer_class = EnrollmentSerializer