from rest_framework import serializers
from .models import Subject, Enrollment  # Changed from Course to Subject

class SubjectSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source="teacher.get_full_name", read_only=True)
    
    class Meta:
        model = Subject  # Changed from Course to Subject
        fields = "__all__"

class EnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enrollment
        fields = "__all__"