import subprocess
import sys
from pathlib import Path
root = Path(__file__).resolve().parent.parent
python = sys.executable
req = root / 'requirements.txt'
log = root / 'pip_install_log.txt'
with open(log, 'w', encoding='utf-8') as f:
    f.write(f'Using python: {python}\n')
    f.write(f'Installing from: {req}\n')
    try:
        proc = subprocess.run([python, '-m', 'pip', 'install', '-r', str(req)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        f.write(proc.stdout)
        f.write('\nEXITCODE=' + str(proc.returncode) + '\n')
    except Exception as e:
        f.write('EXCEPTION:\n')
        f.write(str(e))
        f.write('\n')
print('WROTE', log)
