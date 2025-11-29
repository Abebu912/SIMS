from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages

def role_required(*allowed_roles):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if request.user.is_authenticated:
                if request.user.role in allowed_roles or request.user.is_superuser:
                    return view_func(request, *args, **kwargs)
            messages.error(request, "You don't have permission to access this page.")
            return redirect('dashboard')
        return wrapper
    return decorator

def admin_required(view_func):
    return login_required(role_required('admin')(view_func))

def teacher_required(view_func):
    return login_required(role_required('teacher')(view_func))

def student_required(view_func):
    return login_required(role_required('student')(view_func))

def registrar_required(view_func):
    return login_required(role_required('registrar')(view_func))

def finance_required(view_func):
    return login_required(role_required('finance')(view_func))
def parent_required(view_func):  # ADD PARENT DECORATOR
    return login_required(role_required('parent')(view_func))