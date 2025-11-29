from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Grade, Transcript
from .serializers import GradeSerializer, TranscriptSerializer

class GradeViewSet(viewsets.ModelViewSet):
    queryset = Grade.objects.all()
    serializer_class = GradeSerializer
    permission_classes = [IsAuthenticated]

class TranscriptViewSet(viewsets.ModelViewSet):
    queryset = Transcript.objects.all()
    serializer_class = TranscriptSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=["get"])
    def my_transcript(self, request):
        student = request.user.student_profile
        transcript = Transcript.objects.get(student=student)
        serializer = TranscriptSerializer(transcript)
        return Response(serializer.data)
