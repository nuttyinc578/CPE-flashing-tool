"""Remember Custom Cube paths without activating saved code on launch."""
import json
import os
from pathlib import Path
import tempfile

SLOT_COUNT = 6
BUNDLED_ORTAIN = 'Bundled: Custom Ortain.tar'
MAX_PATH = 4096
MAX_CONFIG = 256 * 1024


def load_slots(file: Path) -> tuple[str, ...]:
    try:
        with file.open('rb') as source:
            raw = source.read(MAX_CONFIG + 1)
        if len(raw) <= MAX_CONFIG:
            data = json.loads(raw)
            if isinstance(data, dict) and data.get('schema') == 1 and isinstance(data.get('paths'), list):
                paths = data['paths'][:SLOT_COUNT]
                clean = tuple(item if isinstance(item, str) and len(item) <= MAX_PATH and '\x00' not in item else ''
                              for item in paths)
                return clean + ('',) * (SLOT_COUNT-len(clean))
    except (OSError, ValueError):
        pass
    return ('',) * SLOT_COUNT


def save_slots(file: Path, paths: tuple[str, ...]) -> None:
    if len(paths) != SLOT_COUNT or any(len(p) > MAX_PATH or '\x00' in p for p in paths):
        raise ValueError('One or more slot paths are too long or invalid.')
    file.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=file.parent, delete=False) as output:
            temporary = Path(output.name)
            json.dump({'schema': 1, 'paths': paths}, output, ensure_ascii=True, indent=2)
        os.replace(temporary, file)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()


def selected_tar(paths: tuple[str, ...], slot: int, ortain: Path) -> Path | None:
    if slot == 0:
        return None
    if not 1 <= slot <= SLOT_COUNT or len(paths) != SLOT_COUNT:
        raise ValueError('Select No overlay or a Custom Cube slot from 1 to 6.')
    value = paths[slot-1].strip()
    if not value:
        raise ValueError(f'Slot {slot} is empty. Browse for a TAR or choose No overlay.')
    if len(value) > MAX_PATH or '\x00' in value:
        raise ValueError(f'Slot {slot} contains an invalid path.')
    return ortain if value == BUNDLED_ORTAIN else Path(value)
