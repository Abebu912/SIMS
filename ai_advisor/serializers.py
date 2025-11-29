from rest_framework import serializers
from .models import AIConversation, AIMessage, SubjectRecommendation

class AIMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIMessage
        fields = "__all__"

class AIConversationSerializer(serializers.ModelSerializer):
    messages = AIMessageSerializer(many=True, read_only=True)
    
    class Meta:
        model = AIConversation
        fields = "__all__"

# subjects/serializers.py
from rest_framework import serializers
from .models import SubjectRecommendation

class SubjectRecommendationSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    subject_code = serializers.CharField(source='subject.code', read_only=True)
    
    class Meta:
        model = SubjectRecommendation
        fields = ['id', 'subject', 'subject_name', 'subject_code', 'confidence_score', 'reason', 'created_at']
