import os
import sys
import traceback

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sims.settings')
# Ensure project root is on sys.path so Django settings can be imported
proj_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)
import django
django.setup()
from importlib import import_module
from django.conf import settings

print("Checking context processors configured in TEMPLATES:\n")
for i, tpl in enumerate(settings.TEMPLATES):
    print(f"Template config #{i}: {tpl.get('NAME', '<no name>')}\n")
    cps = tpl.get('OPTIONS', {}).get('context_processors', [])
    for cp in cps:
        try:
            module_name, fn_name = cp.rsplit('.', 1)
            module = import_module(module_name)
            fn = getattr(module, fn_name)
            try:
                res = fn(None)
            except TypeError:
                res = fn()
            except Exception:
                # try with a fake request object
                class DummyReq: pass
                try:
                    res = fn(DummyReq())
                except Exception as e:
                    raise
            ok = isinstance(res, dict)
            print(f"  {cp} -> {type(res)} {'OK' if ok else 'NOT DICT'}")
            if not ok:
                print("    repr:", repr(res))
        except Exception:
            print(f"  ERROR calling {cp}")
            traceback.print_exc()
    print()

print('Done.')
