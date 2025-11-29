from rest_framework import serializers
from .models import Grade, Transcript

class GradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grade
        fields = "__all__"

class TranscriptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transcript
        fields = "__all__"
