import subprocess
import sys

requirements = [
    'requests',
    'beautifulsoup4',
    'tqdm',
    'mutagen'
]

def install(package):
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])

for req in requirements:
    install(req)

print("Dependencies installed. Install m4b-merge/m4binder manually per their docs.")
