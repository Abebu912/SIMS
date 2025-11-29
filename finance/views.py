from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, Count
from django.http import HttpResponse
from users.decorators import finance_required
from users.models import User
from payments.models import Payment, FeeStructure
# `courses` app may not be present in all deployments; import defensively
try:
    from courses.models import Course
except Exception:
    Course = None
import csv
from datetime import datetime, timedelta

@finance_required
def finance_dashboard(request):
    # Financial statistics
    total_revenue = Payment.objects.filter(status='completed').aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
    pending_payments = Payment.objects.filter(status='pending').count()
    total_fee_structures = FeeStructure.objects.filter(is_active=True).count()
    
    # Recent payments
    recent_payments = Payment.objects.select_related('student', 'fee_structure').order_by('-payment_date')[:10]
    
    context = {
        'total_revenue': total_revenue,
        'pending_payments': pending_payments,
        'total_fee_structures': total_fee_structures,
        'recent_payments': recent_payments,
    }
    return render(request, 'finance/finance_dashboard.html', context)

@finance_required
def fee_tracking(request):
    payments = Payment.objects.all().select_related('student', 'fee_structure').order_by('-payment_date')
    
    # Filters
    status_filter = request.GET.get('status')
    student_filter = request.GET.get('student')
    
    if status_filter:
        payments = payments.filter(status=status_filter)
    if student_filter:
        payments = payments.filter(student__username__icontains=student_filter)
    
    context = {
        'payments': payments,
        'status_choices': Payment.STATUS_CHOICES,
    }
    return render(request, 'finance/fee_tracking.html', context)

@finance_required
def process_payments(request):
    pending_payments = Payment.objects.filter(status='pending').select_related('student', 'fee_structure')
    
    if request.method == 'POST':
        payment_id = request.POST.get('payment_id')
        action = request.POST.get('action')
        payment = get_object_or_404(Payment, id=payment_id)
        
        if action == 'approve':
            payment.status = 'completed'
            messages.success(request, f'Payment approved for {payment.student.username}.')
        elif action == 'reject':
            payment.status = 'failed'
            messages.success(request, f'Payment rejected for {payment.student.username}.')
        
        payment.save()
        return redirect('process_payments')
    
    context = {
        'pending_payments': pending_payments,
    }
    return render(request, 'finance/process_payments.html', context)

@finance_required
def update_fee_policies(request):
    fee_structures = FeeStructure.objects.all()
    
    if request.method == 'POST':
        if 'create' in request.POST:
            name = request.POST.get('name')
            amount = request.POST.get('amount')
            description = request.POST.get('description')
            
            FeeStructure.objects.create(
                name=name,
                amount=amount,
                description=description,
                created_by=request.user
            )
            messages.success(request, 'Fee structure created successfully!')
        
        elif 'update' in request.POST:
            fee_id = request.POST.get('fee_id')
            fee_structure = get_object_or_404(FeeStructure, id=fee_id)
            fee_structure.name = request.POST.get('name')
            fee_structure.amount = request.POST.get('amount')
            fee_structure.description = request.POST.get('description')
            fee_structure.save()
            messages.success(request, 'Fee structure updated successfully!')
        
        elif 'toggle' in request.POST:
            fee_id = request.POST.get('fee_id')
            fee_structure = get_object_or_404(FeeStructure, id=fee_id)
            fee_structure.is_active = not fee_structure.is_active
            fee_structure.save()
            status = 'activated' if fee_structure.is_active else 'deactivated'
            messages.success(request, f'Fee structure {status} successfully!')
        
        return redirect('update_fee_policies')
    
    context = {
        'fee_structures': fee_structures,
    }
    return render(request, 'finance/update_fee_policies.html', context)

@finance_required
def generate_financial_reports(request):
    # Date range for reports
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)  # Last 30 days
    
    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        report_type = request.POST.get('report_type')
    
    # Financial data
    revenue_data = Payment.objects.filter(
        status='completed',
        payment_date__range=[start_date, end_date]
    ).values('payment_date__date').annotate(total=Sum('amount_paid')).order_by('payment_date__date')
    
    fee_type_data = Payment.objects.filter(
        status='completed',
        payment_date__range=[start_date, end_date]
    ).values('fee_structure__name').annotate(
        total=Sum('amount_paid'),
        count=Count('id')
    )
    
    context = {
        'revenue_data': list(revenue_data),
        'fee_type_data': list(fee_type_data),
        'start_date': start_date,
        'end_date': end_date,
    }
    
    if request.GET.get('format') == 'csv':
        return generate_financial_csv(revenue_data, fee_type_data)
    
    return render(request, 'finance/financial_reports.html', context)

def generate_financial_csv(revenue_data, fee_type_data):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="financial_report.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Date', 'Revenue'])
    
    for item in revenue_data:
        writer.writerow([item['payment_date__date'], item['total']])
    
    writer.writerow([])
    writer.writerow(['Fee Type', 'Total Revenue', 'Payment Count'])
    
    for item in fee_type_data:
        writer.writerow([item['fee_structure__name'], item['total'], item['count']])
    
    return response