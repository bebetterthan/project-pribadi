import subprocess
import traceback

path = r'C:\Tools\nuclei.exe'
print(f'Testing: {path}')

try:
    r = subprocess.run(
        [path, '-version'], 
        capture_output=True, 
        timeout=5, 
        text=True
    )
    print(f'✅ Success! Return code: {r.returncode}')
    print(f'Stdout length: {len(r.stdout)}')
    print(f'Stderr length: {len(r.stderr)}')
    print(f'Stderr content: {r.stderr[:200]}')
except FileNotFoundError as e:
    print(f'❌ FileNotFoundError: {e}')
except Exception as e:
    print(f'❌ Exception: {type(e).__name__}: {e}')
    traceback.print_exc()

