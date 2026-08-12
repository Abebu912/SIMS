from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Grade, Transcript, GradeChangeLog
from .serializers import GradeSerializer, TranscriptSerializer

class GradeViewSet(viewsets.ModelViewSet):
    queryset = Grade.objects.all()
    serializer_class = GradeSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        grade_obj = serializer.save()
        # If the creating teacher submits a grade to 'submitted', route to student's homeroom
        if grade_obj.status == 'submitted' and not grade_obj.submitted_to:
            try:
                homeroom = grade_obj.student.studentprofile.homeroom
            except Exception:
                homeroom = None
            if homeroom:
                grade_obj.submitted_to = homeroom
                grade_obj.save(update_fields=['submitted_to'])

    def perform_update(self, serializer):
        # Capture previous state, then save and create a change log with the acting user
        instance = serializer.instance
        try:
            previous = Grade.objects.get(pk=instance.pk)
        except Grade.DoesNotExist:
            previous = None

        updated = serializer.save()

        if previous:
            fields_changed = (
                previous.grade != updated.grade or
                previous.remarks != updated.remarks or
                previous.status != updated.status or
                previous.teacher_id != updated.teacher_id
            )
            if fields_changed:
                GradeChangeLog.objects.create(
                    grade=updated,
                    previous_grade=previous.grade,
                    previous_remarks=previous.remarks,
                    previous_teacher=previous.teacher,
                    changed_by=self.request.user,
                    note='Updated via API by user'
                )

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
