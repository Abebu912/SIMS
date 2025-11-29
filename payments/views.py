from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import FeeStructure, Payment
from .serializers import FeeStructureSerializer, PaymentSerializer
import uuid

class FeeStructureViewSet(viewsets.ModelViewSet):
    queryset = FeeStructure.objects.all()
    serializer_class = FeeStructureSerializer
    permission_classes = [IsAuthenticated]

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=["post"])
    def process_payment(self, request):
        student = request.user.student_profile
        data = request.data
        payment = Payment.objects.create(
            student=student,
            amount=data["amount"],
            transaction_id=str(uuid.uuid4()),
            due_date=data["due_date"],
            status="completed"
        )
        return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=["get"])
    def my_payments(self, request):
        student = request.user.student_profile
        payments = Payment.objects.filter(student=student)
        serializer = PaymentSerializer(payments, many=True)
        return Response(serializer.data)
