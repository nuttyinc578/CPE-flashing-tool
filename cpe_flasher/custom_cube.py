"""Explicitly trusted Python game overlays, staged before rebuilding."""
import json
import shutil
from pathlib import PurePosixPath
from .nuttyroot import extract_tar, digest

PROTECTED = {'cpeloader.py', 'cpeloader_ui.py', 'flashed_runtime.py', 'custom_cube_loading.py',
             'cpeloader_core_runtime.js', 'cpeloader_core.rb', 'root_mode_runtime.py',
             'root_mode_loader.py', 'nuttymod_root_support.py'}


def stage_custom_cube(archive, build, portable, workspace):
    from .core import FlasherError
    stage = workspace/'custom-cube'
    extract_tar(archive, stage)
    try:
        manifest = json.loads((stage/'custom-cube.json').read_text(encoding='utf-8'))
        if not isinstance(manifest, dict): raise ValueError('manifest object required')
        if manifest.get('api') != 'CubeBeta/1' or manifest.get('schema') != 1: raise ValueError('manifest API')
        files = manifest['files']
        if not isinstance(files, dict) or not files or len(files) > 500: raise ValueError('files inventory')
        validated = []
        for name, checksum in files.items():
            parts = PurePosixPath(name).parts
            if len(parts) < 2 or parts[0] != 'python': raise ValueError('files must be under python/')
            relative = PurePosixPath(*parts[1:])
            source = (stage/name).resolve()
            target = (build/str(relative)).resolve()
            if not source.is_relative_to(stage.resolve()) or not target.is_relative_to(build.resolve()): raise ValueError('file location')
            if len(relative.parts) != 1 or relative.name.casefold() in PROTECTED or relative.suffix not in {'.py', '.png', '.ico'}:
                raise ValueError('only root-level Python/artwork overlays; loader components remain managed')
            if not source.is_file() or digest(source) != checksum: raise ValueError('file checksum')
            if relative.suffix == '.py': compile(source.read_text(encoding='utf-8-sig'), name, 'exec')
            validated.append((source, target))
        startup = manifest.get('startup')
        if startup is not None and (startup not in files or not startup.endswith('.py')): raise ValueError('startup entry')
        name = manifest['name']
        if not isinstance(name, str) or not name.strip() or len(name) > 80: raise ValueError('package name')
    except (OSError, ValueError, KeyError, TypeError, SyntaxError) as exc:
        raise FlasherError('Invalid Custom Cube Beta package: '+str(exc)) from exc
    for source, target in validated: shutil.copy2(source, target)
    profile = json.loads((portable/'cpe-flash-profile.json').read_text(encoding='utf-8'))
    if startup:
        relative = 'flash_scripts/custom-cube-startup.py'
        (portable/'flash_scripts').mkdir(exist_ok=True)
        shutil.copy2(stage/startup, portable/relative)
        profile['scripts'].append(relative)
    profile['custom_cube'] = {'name': name, 'version': str(manifest.get('version', 'custom')), 'sha256': digest(archive)}
    from cpeloader import write_json
    for root in (build, portable): write_json(root/'cpe-flash-profile.json', profile)
    return name
