from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.finance_dashboard, name='finance_dashboard'),
    path('fee-tracking/', views.fee_tracking, name='fee_tracking'),
    path('process-payments/', views.process_payments, name='process_payments'),
    path('fee-policies/', views.update_fee_policies, name='update_fee_policies'),
    path('financial-reports/', views.generate_financial_reports, name='financial_reports'),
]