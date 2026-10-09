"""Find game compilers without falling back to Codex's own interpreter or cwd."""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

LAYOUTS = ('python.exe', 'Scripts/python.exe', '.venv/Scripts/python.exe', 'venv/Scripts/python.exe')


def layouts():
    root = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parents[1]))
    try:
        data = json.loads((root/'flashing.patch').read_text(encoding='utf-8'))
        choices = data['python_candidates']
        if data.get('schema') == 1 and isinstance(choices, list) and choices and all(p in LAYOUTS for p in choices):
            return tuple(choices)
    except (OSError, ValueError, KeyError, TypeError): pass
    return LAYOUTS


def eligible(path):
    path = Path(path).resolve()
    if any(p.casefold() in {'.codex', 'codex-runtimes'} for p in path.parts): return False
    if getattr(sys, 'frozen', False) and path == Path(sys.executable).resolve(): return False
    return path.name.casefold() in {'python.exe', 'python3.exe'} and path.is_file()


def resolve_python(selected):
    path = Path(selected).expanduser().resolve()
    candidates = [path/p for p in layouts()] if path.is_dir() else [path]
    for candidate in candidates:
        if eligible(candidate): return candidate.resolve()
    raise ValueError('Choose python.exe or its installation/venv folder. Codex runtimes and the flasher EXE cannot compile the game.')


def discover_python(preferred=()):
    candidates = list(preferred)
    local = os.environ.get('LOCALAPPDATA')
    if local:
        installations = Path(local)/'Programs'/'Python'
        if installations.is_dir(): candidates.extend(sorted(installations.glob('Python*'), reverse=True))
    if os.name == 'nt':
        import winreg
        for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            try:
                with winreg.OpenKey(hive, r'Software\Python\PythonCore') as key:
                    for i in range(winreg.QueryInfoKey(key)[0]):
                        version = winreg.EnumKey(key, i)
                        try:
                            with winreg.OpenKey(key, version+r'\InstallPath') as install:
                                candidates.append(Path(winreg.QueryValue(install, None)))
                        except OSError: pass
            except OSError: pass
    found = shutil.which('python.exe')
    if found: candidates.append(Path(found))
    result = []
    for candidate in candidates:
        try: resolved = resolve_python(candidate)
        except (ValueError, OSError): continue
        if resolved not in result: result.append(resolved)
    return result


def check_python(selected, cwd=None):
    python = resolve_python(selected)
    script = "import sys,importlib.util,json; print(json.dumps({'version':list(sys.version_info[:3]),'missing':[n for n in ('pygame','pymunk','PyInstaller') if importlib.util.find_spec(n) is None]}))"
    try:
        result = subprocess.run([str(python), '-c', script], cwd=cwd, capture_output=True,
                                text=True, timeout=15, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        info = json.loads(result.stdout.strip().splitlines()[-1])
    except (OSError, subprocess.TimeoutExpired, ValueError, IndexError) as exc:
        raise ValueError('Selected Python could not be checked. Select a working Python installation.') from exc
    if result.returncode or tuple(info['version']) < (3, 11):
        raise ValueError('Python 3.11+ is required; Python 3.12 is recommended.')
    if info['missing']:
        raise ValueError('Missing compiler packages: '+', '.join(info['missing'])+'. Install them for this interpreter in PowerShell:\n& "'+str(python)+'" -m pip install pygame pymunk pyinstaller')
    return python
