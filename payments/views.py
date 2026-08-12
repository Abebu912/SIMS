from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import FeeStructure, Payment
from .serializers import FeeStructureSerializer, PaymentSerializer
import uuid
from django.shortcuts import get_object_or_404
from users.models import StudentProfile
from users.models import FinanceProfile
from decimal import Decimal

from django.db import transaction

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
        user = request.user
        # Expecting `fee_structure_id` in request.data. Amount taken from FeeStructure.
        fee_id = request.data.get('fee_structure_id') or request.data.get('fee_id')
        if not fee_id:
            return Response({'detail': 'fee_structure_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

        fee = get_object_or_404(FeeStructure, pk=fee_id)

        try:
            student_profile = user.studentprofile
        except Exception:
            return Response({'detail': 'Student profile not found.'}, status=status.HTTP_400_BAD_REQUEST)

        amount = fee.amount

        # Check balance and process transaction atomically
        with transaction.atomic():
            if student_profile.balance < amount:
                return Response({'detail': 'Insufficient balance to pay. Unable to process payment.'}, status=status.HTTP_400_BAD_REQUEST)

            payment = Payment.objects.create(
                student=user,
                fee_structure=fee,
                amount_paid=amount,
                payment_method=request.data.get('payment_method', 'balance'),
                transaction_id=str(uuid.uuid4()),
                status='completed'
            )

            # Deduct balance
            student_profile.balance = student_profile.balance - amount
            student_profile.save()

            # Credit school's finance account
            try:
                fin = FinanceProfile.objects.select_for_update().filter(user__role='finance', user__is_active=True).first()
                if fin:
                    fin.balance = (fin.balance or Decimal('0.00')) + Decimal(str(amount))
                    fin.save()
            except Exception:
                pass

        return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=["get"])
    def my_payments(self, request):
        # Use the studentprofile OneToOne relation on User
        student = getattr(request.user, 'studentprofile', None)
        payments = Payment.objects.filter(student=request.user)
        serializer = PaymentSerializer(payments, many=True)
        return Response(serializer.data)
