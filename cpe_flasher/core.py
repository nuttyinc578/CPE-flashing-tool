from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import uuid
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Callable

from cpeloader import CPELoader, COMPONENTS, MUTABLE, EXCLUDED_DIRS, write_json
from .nuttyroot import NuttyRootInputs, stage_nuttyroot
from .python_discovery import check_python

EXE = 'The Cube Beta Halloween Update.exe'
Log = Callable[[str], None]


class FlasherError(RuntimeError): pass


@dataclass
class FlashOptions:
    userdata: Path
    loader: Path | None = None
    scripts: tuple[Path, ...] = ()
    verbose_python: bool = False
    safety_cube_alerts: bool = False
    full_rewrite: bool = True
    nuttymod_root: NuttyRootInputs | None = None
    allow_unlocked_updates: bool = False


def validate_options(options: FlashOptions | None) -> FlashOptions:
    if options is None: raise FlasherError('Userdata is required. Create or choose a userdata folder in the flasher.')
    try: data = json.loads((options.userdata/'userdata.json').read_text(encoding='utf-8'))
    except (ValueError, OSError) as exc: raise FlasherError('Userdata needs a valid userdata.json with schema: 1.') from exc
    if not isinstance(data, dict) or data.get('schema') != 1:
        raise FlasherError('Userdata must be a JSON object with schema: 1.')
    for path in (*options.scripts, *((options.loader,) if options.loader else ())):
        if not path.is_file() or path.is_symlink() or path.suffix.lower() != '.py':
            raise FlasherError('Optional loaders and startup scripts must be trusted .py files.')
    return options


def apply_options(options: FlashOptions, build: Path, portable: Path) -> None:
    if not (build/'flashed_runtime.py').is_file():
        raise FlasherError('Select updated complete game source with flashed_runtime.py for userdata support.')
    copy_tree(options.userdata, portable/'userdata')
    scripts = []
    loader = None
    for index, path in enumerate((*((options.loader,) if options.loader else ()), *options.scripts)):
        relative = 'flash_scripts/'+str(index)+'-'+path.name
        destination = portable/relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
        if options.loader and index == 0: loader = relative
        else: scripts.append(relative)
    profile = {'schema': 1, 'game_root': True, 'loader': loader, 'scripts': scripts,
               'verbose_python': options.verbose_python, 'safety_cube_alerts': options.safety_cube_alerts,
               'cpeloader_warning': True, 'full_rewrite': options.full_rewrite,
               'allow_unlocked_updates': options.allow_unlocked_updates,
               'nuttymod_mods': ['cpeloader-unlocked-updates'] if options.allow_unlocked_updates else []}
    for root in (build, portable): write_json(root/'cpe-flash-profile.json', profile)


def safe_extract(archive: Path, destination: Path) -> None:
    destination = destination.resolve()
    with zipfile.ZipFile(archive) as bundle:
        total = 0
        seen = set()
        if len(bundle.infolist()) > 20000: raise FlasherError('ZIP has too many files.')
        for item in bundle.infolist():
            name = item.filename.replace('\\', '/')
            parts = PurePosixPath(name).parts
            if not parts or name.startswith('/') or any(part in {'..', '.'} or ':' in part or part.endswith((' ', '.')) for part in parts):
                raise FlasherError('ZIP contains an unsafe path.')
            if stat.S_ISLNK(item.external_attr >> 16): raise FlasherError('ZIP symbolic links are not supported.')
            target = destination.joinpath(*parts).resolve()
            if not target.is_relative_to(destination): raise FlasherError('ZIP path leaves staging.')
            key = str(target).casefold()
            if key in seen: raise FlasherError('ZIP contains duplicate or case-conflicting paths.')
            seen.add(key)
            total += item.file_size
            if total > 2 * 1024**3: raise FlasherError('ZIP exceeds the 2 GB unpacked limit.')
            if item.is_dir(): target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with bundle.open(item) as source, target.open('wb') as output:
                    shutil.copyfileobj(source, output)


def find_portable(root: Path) -> Path:
    candidates = [p.parent for p in root.rglob(EXE)]
    if len(candidates) != 1: raise FlasherError('Choose a portable ZIP with exactly one current Cube Beta game executable.')
    game = candidates[0]
    if not all((game/name).is_file() for name in COMPONENTS):
        raise FlasherError('This portable ZIP predates CPELoader. Download the updated portable release.')
    if not (game/'cpeloader_manifest.json').is_file(): raise FlasherError('Portable ZIP has no integrity manifest.')
    changes = CPELoader(game).changes()
    # Older official manifests excluded bin folders. Verify every old managed
    # file while allowing the one already-shipped Go helper to migrate policy.
    legacy_helper = 'cpe/go-cache/bin/cpe-go-cache.exe'
    try: baseline = json.loads((game/'cpeloader_manifest.json').read_text(encoding='utf-8'))['files']
    except (ValueError, OSError, KeyError, TypeError): baseline = {}
    if legacy_helper not in baseline: changes = [name for name in changes if name != legacy_helper]
    if changes: raise FlasherError('Portable ZIP does not match its release integrity manifest. Use an original download.')
    return game


def copy_tree(source: Path, destination: Path) -> None:
    for path in source.rglob('*'):
        if path.is_symlink(): raise FlasherError(f'Symbolic links are not supported: {path}')
        if path.is_file() and '__pycache__' not in path.parts:
            target = destination/path.relative_to(source)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)


def source_root(folder: Path) -> Path:
    required = ('the_cube_beta_summer.py', 'cube_core.py', 'summer_build.spec', 'cpeloader.py', 'cpe/backend.py')
    if not all((folder/name).is_file() for name in required):
        raise FlasherError('Recompilation needs complete, matching game source. An EXE cannot be recompiled by itself.')
    return folder


def stage_source(folder: Path, destination: Path) -> None:
    source_root(folder)
    destination.mkdir(parents=True, exist_ok=True)
    # Only game build inputs, never caches, credentials, local state or backups.
    for path in folder.iterdir():
        if path.is_file() and (path.suffix.lower() in {'.py', '.rb', '.js', '.ico', '.png', '.spec', '.txt', '.cmd'} or path.name in {'cpe-backend.json', 'cpe-flash-profile.json', 'rootmode_manifest.json', 'fall_music.mp3', 'click.mp3'}):
            if path.name not in {'cpeloader_state.json', 'cpeloader_manifest.json'}:
                shutil.copy2(path, destination/path.name)
    for name in ('cpe', 'cpe_rephysics', 'cpe_project', 'addons', 'themes', 'repair_payload'):
        if (folder/name).is_dir():
            for path in (folder/name).rglob('*'):
                if path.is_file() and not any(part in {'__pycache__', 'bin', 'obj', 'out', 'tests', 'test', 'node_modules', 'update_backups'} for part in path.relative_to(folder).parts) and not path.name.startswith('.'):
                    if path.is_symlink(): raise FlasherError('Game source contains a symbolic link.')
                    target = destination/path.relative_to(folder)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(path, target)


def pack_source(folder: Path, archive: Path) -> None:
    # Reuse the exact staging policy used by the GUI for release source bundles.
    stage = archive.parent/('source-'+uuid.uuid4().hex)
    stage_source(folder, stage)
    try:
        with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as bundle:
            for path in stage.rglob('*'):
                if path.is_file(): bundle.write(path, path.relative_to(stage).as_posix())
    finally: shutil.rmtree(stage)


def apply_project(project: Path | None, build: Path, portable: Path) -> str:
    rephysics = project/'cpe_rephysics' if project is not None else None
    if project is None or (rephysics is not None and (rephysics/'__init__.py').is_file()):
        if rephysics is not None:
            for root in (build, portable):
                destination = root/'cpe_rephysics'
                if not destination.resolve().is_relative_to(root.resolve()): raise FlasherError('Unsafe staging package path.')
                if destination.exists(): shutil.rmtree(destination)
                copy_tree(rephysics, destination)
        configuration = {'backend': 'rephysics', 'version': '0.1.0', 'flashed_by': 'CPE Flasher Tool'}
        copy_tree(build/'cpe_rephysics', portable/'cpe_rephysics')
        label = 'CPE Rephysics'
    else:
        try: manifest = json.loads((project/'cpe-project.json').read_text(encoding='utf-8'))
        except (OSError, ValueError) as exc: raise FlasherError('Custom projects need a cpe-project.json manifest.') from exc
        if not isinstance(manifest, dict) or manifest.get('api') != 'CPE/1': raise FlasherError('Project must declare api: CPE/1.')
        package = project/'cpe_project'
        if not all((package/name).is_file() for name in ('__init__.py', 'physics.py')):
            raise FlasherError('Project needs cpe_project/__init__.py and physics.py with the CPE-compatible APIs.')
        copy_tree(package, build/'cpe_project')
        copy_tree(package, portable/'cpe_project')
        configuration = {'backend': 'project', 'version': str(manifest.get('version', 'experimental')), 'flashed_by': 'CPE Flasher Tool'}
        label = str(manifest.get('name', 'Custom CPE project'))
    for root in (build, portable): write_json(root/'cpe-backend.json', configuration)
    return label


def run_checked(command: list[str], cwd: Path, log: Log) -> None:
    environment = os.environ.copy()
    environment['PYINSTALLER_CONFIG_DIR'] = str(cwd/'build'/'pyinstaller-cache')
    process = subprocess.Popen(command, cwd=cwd, env=environment, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               text=True, encoding='utf-8', errors='replace', creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    assert process.stdout is not None
    for line in process.stdout: log(line.rstrip())
    if process.wait() != 0: raise FlasherError('Build failed. The installed game has not been replaced. See the build log.')


def compile_game(build: Path, python: Path, log: Log) -> Path:
    try: python = check_python(python, cwd=build)
    except ValueError as exc: raise FlasherError(str(exc)) from exc
    log('Game compiler: '+str(python))
    run_checked([str(python), '-c', "import sys,pygame,pymunk,PyInstaller; assert sys.version_info >= (3,11), 'Python 3.11+ required'"], build, log)
    run_checked([str(python), '-c', "from cpe.backend import CubePhysicsEngine, physics_backend; e=CubePhysicsEngine(); e.execute_line('CPE/1 1 2 200 100 20 1 255 90 30'); e.step(1/60); assert e.snapshot()['engine']=='CPE'; assert hasattr(e,'register_body') and hasattr(physics_backend,'Body')"], build, log)
    run_checked([str(python), '-m', 'PyInstaller', '--noconfirm', '--clean', 'summer_build.spec'], build, log)
    output = build/'dist'/EXE
    if not output.is_file() or output.stat().st_size < 1024: raise FlasherError('Compiler did not produce a game executable.')
    return output


def create_shortcut(target: Path, destination: Path) -> None:
    if os.name != 'nt': raise FlasherError('Windows shortcuts require Windows.')
    script = "$s=(New-Object -ComObject WScript.Shell).CreateShortcut($env:CPE_SHORTCUT);$s.TargetPath=$env:CPE_TARGET;$s.WorkingDirectory=$env:CPE_DIRECTORY;$s.IconLocation=$env:CPE_TARGET+',0';$s.Save()"
    environment = os.environ.copy()
    environment.update(CPE_SHORTCUT=str(destination), CPE_TARGET=str(target/EXE), CPE_DIRECTORY=str(target))
    result = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-WindowStyle', 'Hidden', '-Command', script],
                            env=environment, capture_output=True, text=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    if result.returncode != 0 or not destination.is_file(): raise FlasherError('Game installed, but shortcut creation failed: '+result.stderr[:300])


@dataclass
class PreparedFlash:
    portable: Path
    target: Path
    output_zip: Path
    label: str
    full_rewrite: bool = True


def prepare_flash(archive: Path, target: Path, workspace: Path, source: Path | None, project: Path | None,
                  python: Path, log: Log = print, compiler=compile_game, options: FlashOptions | None = None) -> PreparedFlash:
    target = target.resolve()
    if not (target/EXE).is_file(): raise FlasherError('Target folder does not contain the current Cube Beta executable.')
    CPELoader(target).require_flash()
    options = validate_options(options)
    if options.nuttymod_root:
        if not options.full_rewrite: raise FlasherError('Root Mode requires Full rewrite enabled.')
        if options.nuttymod_root.rootmode_tar is None: raise FlasherError('Select required rootmode.tar library.')
        for path in (options.nuttymod_root.loader_zip, options.nuttymod_root.root_tar,
                     options.nuttymod_root.verification_tar, options.nuttymod_root.official_checksums,
                     options.nuttymod_root.rootmode_tar):
            if not path.is_file(): raise FlasherError('Select all NuttyMod Root package files and official SHA256SUMS.txt.')
    workspace = workspace.resolve()
    if workspace.is_relative_to(options.userdata.resolve()) or options.userdata.resolve().is_relative_to(workspace):
        raise FlasherError('Userdata and staging must be separate folders.')
    if workspace == target or workspace.is_relative_to(target) or target.is_relative_to(workspace):
        raise FlasherError('Staging must be separate from the installed game.')
    workspace.mkdir(parents=True, exist_ok=False)
    log('Validating and extracting the portable ZIP…')
    safe_extract(archive, workspace/'portable')
    portable = find_portable(workspace/'portable')
    build = workspace/'game-build'
    if source is not None: stage_source(source, build)
    elif (portable/'game-source.zip').is_file():
        safe_extract(portable/'game-source.zip', build)
        source_root(build)
    else: raise FlasherError('Older portable ZIP: select matching game source for recompilation.')
    # Update our owned loader policy inside both the compiled game and sidecars.
    runtime_root = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parents[1]))
    shutil.copy2(runtime_root/'cpeloader.py', build/'cpeloader.py')
    for name in ('cpeloader_ui.py', 'halloween_update.py'):
        if (runtime_root/'game_overrides'/name).is_file():
            shutil.copy2(runtime_root/'game_overrides'/name, build/name)
    label = apply_project(project, build, portable)
    apply_options(options, build, portable)
    if options.nuttymod_root:
        label += ' + ' + stage_nuttyroot(options.nuttymod_root, options.loader, archive, build, portable, workspace)
    log(f'Rebuilding the whole game for {label}. Target files remain untouched…')
    executable = compiler(build, python, log)
    # Replace source sidecars too, not only the compiled executable.
    if options.full_rewrite:
        for old in list(portable.rglob('*')):
            relative = old.relative_to(portable)
            if (old.is_file() and old.suffix in {'.py', '.rb', '.js'}
                and (len(relative.parts) == 1 or relative.parts[0] in {'cpe', 'cpe_rephysics', 'cpe_project', 'addons', 'themes', 'repair_payload'})
                and not (build/relative).is_file()):
                old.unlink()  # Only the validated staging copy, never the installed game.
        stage_source(build, portable)
    # Keep patched loader/source sidecars aligned with the newly rebuilt game.
    for name in COMPONENTS: shutil.copy2(build/name, portable/name)
    shutil.copy2(executable, portable/EXE)
    pack_source(build, portable/'game-source.zip')
    write_json(portable/'cpeloader_state.json', CPELoader(target).state())
    if not CPELoader(portable).unlocked: raise FlasherError('Flashed portable did not retain the unlocked loader state.')
    # Never reseal flashed files: keep the original release's trusted baseline.
    output = workspace/'The-Cube-Beta-Flashed-Portable.zip'
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as bundle:
        for path in portable.rglob('*'):
            if path.is_file(): bundle.write(path, path.relative_to(portable).as_posix())
    log(f'Flashed ZIP created: {output}')
    return PreparedFlash(portable, target, output, label, options.full_rewrite)


def install_flash(plan: PreparedFlash, log: Log = print, shortcut=create_shortcut) -> Path:
    target = plan.target.resolve()
    CPELoader(target).require_flash()  # Recheck; the game may have been relocked while compiling.
    if plan.portable.resolve().is_relative_to(target): raise FlasherError('Invalid installation staging path.')
    files = [p for p in plan.portable.rglob('*') if p.is_file()]
    for path in files:
        relative = path.relative_to(plan.portable)
        destination = target/relative
        if path.is_symlink() or not destination.resolve().is_relative_to(target): raise FlasherError('Installation path is unsafe.')
        if relative.parts[0] in {'backup', 'backups'} or destination.name.startswith('unins'):
            raise FlasherError('Portable ZIP tries to replace backup or uninstaller files.')
    backup = target/'backup'/'cpe-flasher'/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+uuid.uuid4().hex[:8])
    if not backup.resolve().is_relative_to(target): raise FlasherError('Unsafe backup directory.')
    backup.mkdir(parents=True)
    records = []
    for path in files:
        relative = path.relative_to(plan.portable)
        destination = target/relative
        if relative.name in MUTABLE and relative.name != 'cpeloader_state.json' and destination.is_file():
            continue  # Keep player settings and runtime data; loader state is transferred explicitly.
        if destination.exists() and not destination.is_file(): raise FlasherError('Target contains a conflicting directory.')
        exists = destination.exists()
        if exists:
            previous = backup/'files'/relative
            previous.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(destination, previous)
        records.append({'path': relative.as_posix(), 'existed': exists})
    if plan.full_rewrite:
        try: managed = json.loads((target/'cpeloader_manifest.json').read_text(encoding='utf-8'))['files']
        except (ValueError, OSError, KeyError, TypeError): raise FlasherError('Full rewrite needs the original managed-file manifest.')
        if not isinstance(managed, dict): raise FlasherError('Invalid managed-file manifest.')
        for name in managed:
            relative = Path(name)
            destination = target/relative
            if relative.is_absolute() or '..' in relative.parts or ':' in name or not destination.resolve().is_relative_to(target):
                raise FlasherError('Unsafe path in managed-file manifest.')
            if relative.name in MUTABLE or any(part in EXCLUDED_DIRS for part in relative.parts) or relative.name.startswith('unins'):
                continue
            if not (plan.portable/relative).exists() and destination.is_file():
                previous = backup/'files'/relative
                previous.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(destination, previous)
                records.append({'path': relative.as_posix(), 'existed': True, 'delete': True})
    link = target/'The Cube Beta.lnk'
    if not any(record['path'] == link.name for record in records):
        if link.is_symlink() or (link.exists() and not link.is_file()): raise FlasherError('Conflicting shortcut path.')
        if link.is_file():
            (backup/'files').mkdir(exist_ok=True)
            shutil.copy2(link, backup/'files'/link.name)
        shortcut_record = {'path': link.name, 'existed': link.is_file()}
    else: shortcut_record = None
    write_json(backup/'manifest.json', {'target': str(target), 'files': records + ([shortcut_record] if shortcut_record else []), 'project': plan.label})
    changed = []
    try:
        for record in records:
            relative = Path(record['path'])
            destination = target/relative
            if record.get('delete'):
                destination.unlink()
                changed.append(record)
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            temporary = destination.with_name(destination.name+'.cpe-flasher-writing')
            shutil.copy2(plan.portable/relative, temporary)
            os.replace(temporary, destination)
            changed.append(record)
    except Exception as exc:
        if 'temporary' in locals() and temporary.is_file(): temporary.unlink()
        for record in reversed(changed):
            destination = target/record['path']
            if record['existed']: shutil.copy2(backup/'files'/record['path'], destination)
            elif destination.is_file(): destination.unlink()
        raise FlasherError(f'Replacement failed and changed files were rolled back. Close the game and retry. Backup: {backup}') from exc
    log(f'Installed {plan.label}. Backup: {backup}')
    # Shortcut creation is deliberately after every game file has been replaced.
    shortcut(target, target/'The Cube Beta.lnk')
    differences = CPELoader(target).changes()
    log(f'Game integrity check detects {len(differences)} changed files. The game will show its warning on launch.')
    return backup


def restore_backup(target: Path, backup: Path, log: Log = print) -> Path:
    """Restore recorded files only; retain a recovery snapshot for undoing restore."""
    target, backup = Path(target).resolve(), Path(backup).resolve()
    base = (target/'backup'/'cpe-flasher').resolve()
    if not base.is_relative_to(target) or backup.parent != base:
        raise FlasherError('Choose a backup inside this game folder: backup/cpe-flasher/<backup>.')
    try: manifest = json.loads((backup/'manifest.json').read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc: raise FlasherError('Backup manifest is missing or unreadable.') from exc
    if not isinstance(manifest, dict) or Path(manifest.get('target', '')).resolve() != target:
        raise FlasherError('Backup belongs to a different game folder.')
    records = manifest.get('files')
    if not isinstance(records, list) or not records: raise FlasherError('Backup has no file records.')
    seen = set()
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get('path'), str) or type(record.get('existed')) is not bool:
            raise FlasherError('Invalid backup file record.')
        name = record['path']; parts = PurePosixPath(name.replace('\\', '/')).parts
        if not parts or name.startswith(('/', '\\')) or any(p in {'.', '..'} or ':' in p or p.endswith((' ', '.')) for p in parts):
            raise FlasherError('Unsupported backup file path.')
        destination = target.joinpath(*parts); previous = backup/'files'/Path(*parts)
        key = str(destination).casefold()
        if key in seen or parts[0].lower() in {'backup', 'backups', '.git', '.codex', '.agents'} or destination.name.startswith('unins'):
            raise FlasherError('Backup contains conflicting or protected file records.')
        seen.add(key)
        if destination.is_symlink() or not destination.resolve().is_relative_to(target) or (destination.exists() and not destination.is_file()):
            raise FlasherError('Restore destination is not a regular game file.')
        if record['existed'] and (previous.is_symlink() or not previous.resolve().is_relative_to(backup/'files') or not previous.is_file()):
            raise FlasherError('Backup file is missing: '+name)
    # Do not require an unlocked or working game: restoring is a recovery action.
    recovery = base/('before-restore-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+uuid.uuid4().hex[:8])
    recovery.mkdir(parents=True)
    current = []
    for record in records:
        path = target/record['path']
        exists = path.is_file()
        if exists:
            saved = recovery/'files'/record['path']; saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, saved)
        current.append({'path': record['path'], 'existed': exists})
    write_json(recovery/'manifest.json', {'target': str(target), 'files': current, 'project': 'Before restoring '+backup.name})
    changed = []
    try:
        for record, original in zip(records, current):
            path = target/record['path']
            if record['existed']:
                path.parent.mkdir(parents=True, exist_ok=True)
                temporary = path.with_name(path.name+'.cpe-flasher-restoring')
                shutil.copy2(backup/'files'/record['path'], temporary)
                os.replace(temporary, path)
            elif path.is_file(): path.unlink()
            changed.append(original)
    except Exception as exc:
        if 'temporary' in locals() and temporary.is_file(): temporary.unlink()
        try:
            for original in reversed(changed):
                path = target/original['path']
                if original['existed']: shutil.copy2(recovery/'files'/original['path'], path)
                elif path.is_file(): path.unlink()
        except Exception as rollback:
            raise FlasherError(f'Restore and rollback failed. Recovery files: {recovery}. Close the game before retrying.') from rollback
        raise FlasherError(f'Restore failed; changes were rolled back. Close the game. Recovery snapshot: {recovery}') from exc
    log(f'Restored {len(records)} recorded files from {backup}. Recovery snapshot: {recovery}')
    return recovery


def locate_games() -> list[Path]:
    candidates = []
    local = os.environ.get('LOCALAPPDATA')
    if local: candidates.append(Path(local)/'Programs'/'The Cube Beta Halloween Update')
    if getattr(sys, 'frozen', False): candidates.append(Path(sys.executable).resolve().parent)
    return list(dict.fromkeys(path.resolve() for path in candidates
                             if (path/EXE).is_file() and all((path/name).is_file() for name in COMPONENTS)))
