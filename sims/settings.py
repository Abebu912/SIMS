import os
from pathlib import Path
from datetime import timedelta

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'your-secret-key-here'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party apps
    'rest_framework',
    'rest_framework_simplejwt',
    
    # Your apps
    'users',
    'students',
    'subjects',
    'ranks',
    'payments',
    'notifications',
    'parents',
    'ai_advisor',
    'teachers'
    ,
    'finance'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'sims.urls'

# Templates configuration
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',  # This points to your main templates folder
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.media',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',  # If you have static files
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Authentication settings
LOGIN_REDIRECT_URL = 'dashboard'  # Where to redirect after login
LOGOUT_REDIRECT_URL = 'home'      # Where to redirect after logout
LOGIN_URL = 'login'               # URL for login page

# If you're using a custom user model
AUTH_USER_MODEL = 'users.User'

# Email configuration (for password reset)
# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
EMAIL_HOST_USER = 'abebuwubete099@gmail.com'
EMAIL_HOST_PASSWORD = 'xsvuarxmynwdvjfh'  # Use App Password, not regular password
DEFAULT_FROM_EMAIL = 'abebuwubete099@gmail.com'
# Passwd reset settings
PASSWORD_RESET_TIMEOUT = 86400  # 24 hours in seconds
SITE_URL = 'http://127.0.0.1:8000'  # Change to your domain in production

# Load persisted site settings from `site_settings.json` (if present) so
# values like `admin_email` persist across server restarts. This overrides
# `DEFAULT_FROM_EMAIL` and `ADMINS` at startup when a valid file exists.
try:
    import json
    settings_path = BASE_DIR / 'site_settings.json'
    if settings_path.exists():
        with open(settings_path, 'r', encoding='utf-8') as f:
            site_settings = json.load(f)
        admin_email = site_settings.get('admin_email') or site_settings.get('admin_email_address') or site_settings.get('admin_email_address')
        # fallback keys: keep backward-compatibility if different keys used
        if admin_email:
            DEFAULT_FROM_EMAIL = admin_email
            ADMINS = [("Site Admin", admin_email)]
except Exception:
    # If the file is missing or invalid, do not prevent Django from starting.
    pass

# Email configuration
# By default development uses the console backend. If SMTP settings are
# provided either in environment variables or in `site_settings.json`, the
# loader below will configure Django to use the SMTP backend so real emails
# can be delivered.
import os
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.environ.get('EMAIL_HOST', '')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 0) or 0)
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'False').lower() in ('1', 'true', 'yes')
EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL', 'False').lower() in ('1', 'true', 'yes')

try:
    # If site_settings.json contains email configuration, prefer it
    if settings_path.exists():
        email_cfg = site_settings.get('email') or site_settings.get('email_settings') or {}
        # Accept top-level keys too
        if not email_cfg:
            email_cfg = {
                'host': site_settings.get('email_host'),
                'port': site_settings.get('email_port'),
                'user': site_settings.get('email_host_user'),
                'password': site_settings.get('email_host_password'),
                'use_tls': site_settings.get('email_use_tls'),
                'use_ssl': site_settings.get('email_use_ssl'),
                'backend': site_settings.get('email_backend'),
            }

        if email_cfg:
            # If an explicit backend provided, use it
            if email_cfg.get('backend'):
                EMAIL_BACKEND = email_cfg.get('backend')

            if email_cfg.get('host'):
                EMAIL_HOST = email_cfg.get('host')
            if email_cfg.get('port'):
                try:
                    EMAIL_PORT = int(email_cfg.get('port'))
                except Exception:
                    pass
            if email_cfg.get('user'):
                EMAIL_HOST_USER = email_cfg.get('user')
            if email_cfg.get('password'):
                EMAIL_HOST_PASSWORD = email_cfg.get('password')
            if email_cfg.get('use_tls') is not None:
                EMAIL_USE_TLS = bool(email_cfg.get('use_tls'))
            if email_cfg.get('use_ssl') is not None:
                EMAIL_USE_SSL = bool(email_cfg.get('use_ssl'))

        # If we have host and port configured, and no explicit backend, use SMTP
        if EMAIL_HOST and EMAIL_PORT and EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend':
            EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
except Exception:
    pass
# Toggle automatic approval of child-link requests when the submitted identifier matches a student
PARENT_CHILD_LINK_AUTO_APPROVE = True
# For production, configure real email settings

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
}

# Auto-enrollment settings
# Which subject types should be auto-assigned to new students (e.g. 'core', 'elective')
AUTO_ENROLL_SUBJECT_TYPES = ['core']
# If True, the system will create Enrollment rows (status='pending') for auto-assigned subjects
AUTO_CREATE_ENROLLMENTS = True