"""Explicitly trusted Python game overlays, staged before rebuilding."""
import json
import shutil
import tarfile
from pathlib import PurePosixPath
from .nuttyroot import extract_tar, digest

PROTECTED = {'cpeloader.py', 'cpeloader_ui.py', 'flashed_runtime.py', 'custom_cube_loading.py',
             'cpeloader_core_runtime.js', 'cpeloader_core.rb', 'root_mode_runtime.py',
             'root_mode_loader.py', 'nuttymod_root_support.py'}


def read_overlay(archive, build, stage):
    from .core import FlasherError
    try:
        extract_tar(archive, stage)
        manifest = json.loads((stage/'custom-cube.json').read_text(encoding='utf-8'))
        if not isinstance(manifest, dict): raise ValueError('manifest object required')
        if manifest.get('api') != 'CubeBeta/1' or manifest.get('schema') != 1: raise ValueError('manifest API')
        files = manifest['files']
        if not isinstance(files, dict) or not files or len(files) > 500: raise ValueError('files inventory')
        validated = []
        for name, checksum in files.items():
            parts = PurePosixPath(name).parts
            if len(parts) != 2 or parts[0] != 'python' or '\\' in name: raise ValueError('files must be directly under python/')
            relative = PurePosixPath(*parts[1:])
            source = (stage/name).resolve()
            target = (build/str(relative)).resolve()
            if not source.is_relative_to(stage.resolve()) or target.parent != build.resolve(): raise ValueError('file location')
            if target.name.casefold() in PROTECTED or relative.suffix not in {'.py', '.png', '.ico'}:
                raise ValueError('only root-level Python/artwork overlays; loader components remain managed')
            if not source.is_file() or digest(source) != checksum: raise ValueError('file checksum')
            if relative.suffix == '.py': compile(source.read_text(encoding='utf-8-sig'), name, 'exec')
            validated.append((source, target))
        startup = manifest.get('startup')
        if startup is not None and (startup not in files or not startup.endswith('.py')): raise ValueError('startup entry')
        name = manifest['name']
        if not isinstance(name, str) or not name.strip() or len(name) > 80: raise ValueError('package name')
        metadata = {'name': name, 'version': str(manifest.get('version', 'custom')), 'sha256': digest(archive)}
    except (OSError, ValueError, KeyError, TypeError, SyntaxError, tarfile.TarError, FlasherError) as exc:
        raise FlasherError(f'Invalid Custom Cube Beta package {archive.name}: {exc}') from exc
    return metadata, validated, stage/startup if startup else None


def stage_custom_cubes(archives, build, portable, workspace):
    from .core import FlasherError
    overlays = []
    owners = {}
    for number, archive in enumerate(archives, 1):
        overlay = read_overlay(archive, build, workspace/'custom-cube'/str(number))
        for _, target in overlay[1]:
            key = target.name.casefold()
            if key in owners:
                raise FlasherError(f'Custom Cube conflict: {owners[key]} and {archive.name} both target '
                                   f'{target.name}. Uncheck one package or use non-overlapping files.')
            owners[key] = archive.name
        overlays.append(overlay)

    profile = json.loads((portable/'cpe-flash-profile.json').read_text(encoding='utf-8'))
    for number, (_, files, startup) in enumerate(overlays, 1):
        for source, target in files:
            shutil.copy2(source, target)
        if startup:
            suffix = f'-{number}' if len(overlays) > 1 else ''
            relative = f'flash_scripts/custom-cube-startup{suffix}.py'
            (portable/'flash_scripts').mkdir(exist_ok=True)
            shutil.copy2(startup, portable/relative)
            profile['scripts'].append(relative)
    profile['custom_cubes'] = [metadata for metadata, _, _ in overlays]
    if len(overlays) == 1:
        profile['custom_cube'] = overlays[0][0]
    from cpeloader import write_json
    for root in (build, portable): write_json(root/'cpe-flash-profile.json', profile)
    return tuple(metadata['name'] for metadata, _, _ in overlays)


def stage_custom_cube(archive, build, portable, workspace):
    return stage_custom_cubes((archive,), build, portable, workspace)[0]
