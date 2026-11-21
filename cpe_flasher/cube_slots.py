"""Remember Custom Cube paths without activating saved code on launch."""
import json
import os
from pathlib import Path
import tempfile

SLOT_COUNT = 6
BUNDLED_ORTAIN = 'Bundled: Custom Ortain.tar'
BUNDLED_BUILD_MODE = 'Bundled: Build Mode.tar'
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


def selected_tars(paths: tuple[str, ...], checked: tuple[bool, ...], ortain: Path,
                  build_mode: Path | None = None) -> tuple[tuple[int, Path], ...]:
    if len(paths) != SLOT_COUNT or len(checked) != SLOT_COUNT:
        raise ValueError(f'Expected {SLOT_COUNT} Custom Cube slots.')
    selected = []
    for slot, (path, enabled) in enumerate(zip(paths, checked), 1):
        if not enabled:
            continue
        value = path.strip()
        if not value:
            raise ValueError(f'Slot {slot} is empty. Browse for a TAR or uncheck it.')
        if len(value) > MAX_PATH or '\x00' in value:
            raise ValueError(f'Slot {slot} contains an invalid path.')
        if value == BUNDLED_BUILD_MODE and build_mode is None:
            raise ValueError('The bundled Build Mode TAR is unavailable. Browse for the package or uncheck the slot.')
        selected.append((slot, ortain if value == BUNDLED_ORTAIN else build_mode if value == BUNDLED_BUILD_MODE else Path(value)))
    return tuple(selected)
