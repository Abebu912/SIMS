import os
import sys
proj = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, proj)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sims.settings')
import django
from django.urls import reverse

django.setup()

try:
    print('finance_dashboard ->', reverse('finance_dashboard'))
except Exception as e:
    print('Error:', type(e), e)
