from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from users import views as user_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', user_views.dashboard, name='dashboard'),
    path('login/', user_views.user_login, name='login'),
    path('register/', user_views.register, name='register'),
    path('logout/', user_views.user_logout, name='logout'),
    
    # Include app URLs
    path('users/', include('users.urls')),
    path('teachers/', include('teachers.urls')),
    path('parents/', include('parents.urls')),
    path('students/', include('students.urls')),
    path('registrar/', include('registrar.urls')),
    path('finance/', include('finance.urls')),
    path('courses/', include('courses.urls')),
    path('payments/', include('payments.urls')),
    path('grades/', include('ranks.urls')),
    path('notifications/', include('notifications.urls')),
    path('ai_advisor/', include('ai_advisor.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)