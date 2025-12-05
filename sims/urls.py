# sims/urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.contrib.auth import views as auth_views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from users.views import register_view
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from users.views import CustomPasswordResetView, CustomPasswordResetDoneView

urlpatterns = [
    
    # Frontend pages
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path("login/", auth_views.LoginView.as_view(template_name='registration/login.html'), name="login"),
    path("register/", register_view, name="register"),
    path("dashboard/", TemplateView.as_view(template_name="dashboards.html"), name="dashboard"),
    path("logout/", auth_views.LogoutView.as_view(next_page='home'), name="logout"),
    
    # Password reset functionality
    path('password-reset/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='registration/password_reset_confirm.html'
         ), 
         name='password_reset_confirm'),
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='registration/password_reset_complete.html'
         ), 
         name='password_reset_complete'),

    # ✅ ADD THIS LINE: Template URLs for students (WEB PAGES)
    path("students/", include("students.urls")),
    # Registrar URLs (admin/registrar area)
    path("registrar/", include("registrar.urls")),
    # Teachers app URLs
    path("teachers/", include("teachers.urls")),
    # Parents app URLs
    path("parents/", include("parents.urls")),
    # expose users URLs under /users/ for backward-compatible links
    path("users/", include("users.urls")),
    # Finance app URLs (enable finance officer pages and named routes)
    path("finance/", include("finance.urls")),
    
    # Admin and API routes
    path('', include('users.urls')),
    path('', lambda request: redirect('users/dashboard/')),
    path("admin/", admin.site.urls),
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/users/", include("users.urls")),
    
    # ✅ KEEP THIS: API URLs for students (API ENDPOINTS)
    path("api/students/", include("students.urls")),
    
    path("api/grades/", include("ranks.urls")),
    path("api/payments/", include("payments.urls")),
    path("api/notifications/", include("notifications.urls")),
    path("api/ai/", include("ai_advisor.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)