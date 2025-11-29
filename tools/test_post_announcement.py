import os, sys
proj = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, proj)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sims.settings')
import django
django.setup()
from django.test.client import RequestFactory
import users.admin_views as admin_views
from users.models import User
from django.contrib.messages.storage.fallback import FallbackStorage

# create admin user
admin, created = User.objects.get_or_create(username='auto_admin', defaults={'role':'admin', 'email':'auto_admin@example.com'})
admin.set_password('pass')
admin.save()

rf = RequestFactory()
req = rf.post('/users/post-announcement/', data={'title':'Test','content':'Hello all','target_roles':[]})
req.user = admin
# Requests created by RequestFactory are not processed through middleware,
# so attach a fallback messages storage (equivalent to MessageMiddleware)
setattr(req, 'session', {})
setattr(req, '_messages', FallbackStorage(req))
resp = admin_views.post_announcement(req)
print('Response type:', type(resp))
if hasattr(resp, 'status_code'):
    print('Status code:', resp.status_code)
print('Done')
