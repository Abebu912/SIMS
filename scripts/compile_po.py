#!/usr/bin/env python3
"""
Compile all gettext .po files under `locale/*/LC_MESSAGES/` into .mo files using polib.
This is a fallback when GNU gettext `msgfmt` is not available on Windows.

Usage:
  pip install polib
  python scripts/compile_po.py

The script will find all .po files and write the corresponding .mo files.
"""
import sys
from pathlib import Path

try:
    import polib
except Exception as e:
    print("polib is required. Install with: pip install polib")
    sys.exit(1)

root = Path(__file__).resolve().parents[1]
locale_dir = root / 'locale'
if not locale_dir.exists():
    print(f"No locale directory found at: {locale_dir}")
    sys.exit(1)

count = 0
for po in locale_dir.rglob('LC_MESSAGES/*.po'):
    mo = po.with_suffix('.mo')
    try:
        pofile = polib.pofile(str(po))
        pofile.save_as_mofile(str(mo))
        print(f"Compiled: {po} -> {mo}")
        count += 1
    except Exception as exc:
        print(f"Failed to compile {po}: {exc}")

if count == 0:
    print("No .po files were compiled. Run `django-admin makemessages -l <lang>` first to generate .po files.")
else:
    print(f"Done. {count} file(s) compiled.")
