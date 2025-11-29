# ultimate_fix.py
import os
import shutil
import subprocess
import sys

def ultimate_fix():
    print("🔥 ULTIMATE FIX STARTING...")
    
    # STEP 1: Check project structure
    print("📁 STEP 1: Checking project structure...")
    if not os.path.exists('manage.py'):
        print("❌ ERROR: manage.py not found! You're in the wrong directory.")
        print("💡 Make sure you're in the folder that contains manage.py")
        return
    
    # STEP 2: Delete ALL migration files
    print("🗑️  STEP 2: Deleting ALL migration files...")
    apps = ['users', 'students', 'teachers', 'courses', 'payments', 'ranks', 
            'notifications', 'ai_advisor', 'registrar', 'finance', 'parents']
    
    for app in apps:
        migrations_dir = os.path.join(app, 'migrations')
        if os.path.exists(migrations_dir):
            for file in os.listdir(migrations_dir):
                file_path = os.path.join(migrations_dir, file)
                if file.endswith('.py') and file != '__init__.py':
                    try:
                        os.remove(file_path)
                        print(f"   ✓ Deleted: {file_path}")
                    except:
                        pass
    
    # STEP 3: Delete database
    print("🗑️  STEP 3: Deleting database files...")
    for db_file in ['db.sqlite3', 'db.sqlite3-wal', 'db.sqlite3-shm']:
        if os.path.exists(db_file):
            os.remove(db_file)
            print(f"   ✓ Deleted: {db_file}")
    
    # STEP 4: Create PERFECT settings.py
    print("⚙️  STEP 4: Creating PERFECT settings.py...")
    
    # First, find the correct settings path
    settings_path = None
    if os.path.exists('sims_proj/settings.py'):
        settings_path = 'sims_proj/settings.py'
    elif os.path.exists('settings.py'):
        settings_path = 'settings.py'
    else:
        print("❌ No settings.py found! Creating in sims_proj/")
        os.makedirs('sims_proj', exist_ok=True)
        settings_path = 'sims_proj/settings.py'
    
    settings_content = '''"""
Django settings for sims_proj project.
ULTIMATE FIX VERSION
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-ultimate-fix-1234567890'

DEBUG = True
ALLOWED_HOSTS = []

# APPLICATION DEFINITION - NO DAPHNE!
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # YOUR CUSTOM APPS
    'users',
    'courses',
    'students',
    'teachers',
    'payments',
    'grades',
    'notifications',
    'ai_advisor',
    'registrar',
    'finance',
    'parents',
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

ROOT_URLCONF = 'sims_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'sims_project.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ⚠️⚠️⚠️ CRITICAL - MUST BE 'users.User' ⚠️⚠️⚠️
AUTH_USER_MODEL = 'users.User'

LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'
LOGIN_URL = 'login'
'''

    with open(settings_path, 'w', encoding='utf-8') as f:
        f.write(settings_content)
    print(f"   ✓ Created perfect settings.py at: {settings_path}")
    
    # STEP 5: Fix users/models.py
    print("📝 STEP 5: Fixing users model...")
    users_model_path = 'users/models.py'
    if os.path.exists(users_model_path):
        with open(users_model_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remove ALL CustomUser references
        content = content.replace('CustomUser', 'User')
        content = content.replace("AUTH_USER_MODEL = 'users.CustomUser'", "AUTH_USER_MODEL = 'users.User'")
        
        with open(users_model_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("   ✓ Fixed users/models.py")
    else:
        print("   ⚠️ users/models.py not found")
    
    # STEP 6: Remove Daphne from any other files
    print("🔧 STEP 6: Removing Daphne references...")
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if 'daphne' in content.lower():
                        new_content = content.replace("'daphne'", "")
                        new_content = new_content.replace('"daphne"', '')
                        new_content = new_content.replace("ASGI_APPLICATION", "# ASGI_APPLICATION")
                        
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        print(f"   ✓ Removed Daphne from: {file_path}")
                except:
                    pass
    
    print("✅ ULTIMATE FIX COMPLETED!")
    print("\\n🚀 NOW RUN THESE COMMANDS:")
    print("   1. python manage.py makemigrations users")
    print("   2. python manage.py makemigrations")
    print("   3. python manage.py migrate")
    print("   4. python manage.py createsuperuser")
    print("   5. python manage.py runserver")

if __name__ == '__main__':
    ultimate_fix()