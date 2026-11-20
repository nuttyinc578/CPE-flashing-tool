"""Free Windows game identities. Reading metadata must never launch the game."""
import ast
from datetime import datetime, timedelta, timezone
from pathlib import Path

HALLOWEEN = 'The Cube Beta Halloween Update.exe'
NIGHTLY = 'The Cube Beta Nightly.exe'
CHRISTMAS = 'The Cube Beta Christmas Update.exe'
OFFICIAL_NAMES = frozenset(n.casefold() for n in (HALLOWEEN, NIGHTLY, CHRISTMAS, 'The Cube Beta Christmas.exe'))
# Exact public free-game release revisions, shared by the flasher and its build.
PROFILE_REVISIONS = {
    '6.4.1': 'ae66b2f2dd20d140b1e405e2656afa8d73e68d7a',
    '6.4.2': '6b474eb045f90a0765098fc8b47ab47283e7d34b',
    '6.4.2-nightly': 'df814c83c735a4f3daba7a354515cc800b0642f7',
    '6.4.3-nightly': '2d10da7cb828cdc3ada3413061b94027ad5918cd',
    '6.4.3-nightly.2': '63a9369a5bf93db6a091453b08757997f7018511',
    '6.4.3-nightly.3': '3b5cf2b5ed3a42dc23c114f91e9a5222fe8a3e30',
}
# Planned stable has no bundled source until its own release exists.
SUPPORTED = (*PROFILE_REVISIONS, '6.4.3')
MODERN_PROFILES = frozenset(SUPPORTED) - {'6.4.1'}
# Midnight December 2, 2026 in Toronto (EST).
CHRISTMAS_DATE = datetime(2026, 12, 2, 5, tzinfo=timezone.utc)

def countdown(now=None):
    remaining = CHRISTMAS_DATE - (now or datetime.now(timezone.utc))
    if remaining <= timedelta(0):
        return 'Christmas update · December 2 has arrived. Check official releases for availability.'
    seconds = (remaining + timedelta(microseconds=999999)) // timedelta(seconds=1)
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return f'Christmas update · December 2, 2026 · {days}d {hours:02}:{minutes:02}:{seconds:02} remaining'

def exe_version(path):
    import pefile
    try:
        with pefile.PE(str(path), fast_load=True) as pe:
            pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_RESOURCE']])
            for group in getattr(pe, 'FileInfo', ()):
                for info in group:
                    for table in getattr(info,'StringTable', ()):
                        raw = table.entries.get(b'ProductVersion')
                        if raw: return raw.decode('utf-8', 'replace').strip().lstrip('v')
    except (pefile.PEFormatError, OSError):
        pass
    return ''

def source_version(folder):
    for name in ('release_info.py', 'cube_core.py'):
        path = Path(folder)/name
        if path.is_file():
            for stmt in ast.parse(path.read_text(encoding='utf-8-sig')).body:
                if isinstance(stmt,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='VERSION' for t in stmt.targets):
                    return stmt.value.value if isinstance(stmt.value,ast.Constant) and isinstance(stmt.value.value,str) else ''
    return ''
