"""NuttyMod Root package assembly. Archive hashes are consistency checks, not signatures."""
import hashlib
import json
import shutil
import tarfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


@dataclass
class NuttyRootInputs:
    loader_zip: Path
    root_tar: Path
    verification_tar: Path
    official_checksums: Path
    rootmode_tar: Path | None = None


def digest(path):
    with Path(path).open('rb') as stream: return hashlib.file_digest(stream, 'sha256').hexdigest()


def extract_tar(archive, destination):
    from .core import FlasherError
    destination = destination.resolve()
    seen, total = set(), 0
    with tarfile.open(archive, 'r:*') as bundle:
        for count, member in enumerate(bundle):
            parts = PurePosixPath(member.name.replace('\\', '/')).parts
            if count >= 10000 or not parts or member.name.startswith(('/', '\\')) or any(p in {'.', '..'} or ':' in p or p.endswith((' ', '.')) for p in parts):
                raise FlasherError('Unsupported TAR path or file count.')
            if not member.isfile() and not member.isdir(): raise FlasherError('TAR links/devices are not supported.')
            target = destination.joinpath(*parts).resolve()
            key = str(target).casefold()
            if not target.is_relative_to(destination) or key in seen: raise FlasherError('TAR has conflicting paths.')
            seen.add(key); total += member.size
            if total > 256 * 1024**2: raise FlasherError('NuttyMod TAR exceeds the 256 MB limit.')
            if member.isdir(): target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with bundle.extractfile(member) as source, target.open('wb') as output: shutil.copyfileobj(source, output)


def stage_nuttyroot(inputs, loader, archive, build, portable, workspace):
    from .core import FlasherError, safe_extract, copy_tree
    if loader is None or loader.name != 'nuttymod_loader.py':
        raise FlasherError('NuttyMod Root requires the readable nuttymod_loader.py entry file.')
    if not (build/'nuttymod_root_support.py').is_file() or 'initialize_nuttymod' not in (build/'flashed_runtime.py').read_text(encoding='utf-8'):
        raise FlasherError('Choose updated complete game source with NuttyMod Root support.')
    checksum = digest(archive)
    try:
        lines = inputs.official_checksums.read_text(encoding='utf-8-sig').splitlines()
        accepted = any(line.split()[0].lower() == checksum and line.split()[-1].lstrip('*').endswith('-Portable.zip') for line in lines if len(line.split()) >= 2)
    except OSError as exc: raise FlasherError('Select SHA256SUMS.txt downloaded from the official game release.') from exc
    if not accepted: raise FlasherError('Portable ZIP does not match the selected official release checksums.')
    stage = workspace/'nuttymod-packages'
    safe_extract(inputs.loader_zip, stage/'loader')
    extract_tar(inputs.root_tar, stage/'root')
    extract_tar(inputs.verification_tar, stage/'verification')
    if inputs.rootmode_tar is None: raise FlasherError('NuttyMod Root requires rootmode.tar library v1.2.')
    extract_tar(inputs.rootmode_tar, stage/'rootmode')
    try:
        verification = json.loads((stage/'verification'/'verification.json').read_text(encoding='utf-8'))
        manifest = json.loads((stage/'root'/'root_manifest.json').read_text(encoding='utf-8'))
        if verification['schema'] != 1 or manifest['schema'] != 1: raise ValueError('schema')
        actual = {'loader_py': digest(loader), 'loader_zip': digest(inputs.loader_zip), 'root_tar': digest(inputs.root_tar)}
        actual['rootmode_tar'] = digest(inputs.rootmode_tar)
        mode = json.loads((stage/'rootmode'/'rootmode_manifest.json').read_text(encoding='utf-8'))
        if mode.get('schema') != 1 or mode.get('library') != '1.2': raise ValueError('Root Mode library')
        for name in ('root_mode_runtime.py', 'root_mode_loader.py'):
            if not (stage/'rootmode'/name).is_file(): raise ValueError('Root Mode core source')
        if verification['sha256'] != actual or verification['version'] != manifest['version']: raise ValueError('package hashes/version')
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise FlasherError('NuttyMod verification TAR does not match the loader ZIP, loader .py and root TAR.') from exc
    entries = list((stage/'loader').rglob('nuttymod_loader.py'))
    if len(entries) != 1 or digest(entries[0]) != actual['loader_py']:
        raise FlasherError('Loader ZIP must contain exactly the matching nuttymod_loader.py.')
    # Normalize the entire loader folder under userdata. Nothing is auto-loaded
    # by the base AddonManager; only the explicitly verified root entry runs.
    data = portable/'userdata'/'nuttymod'
    copy_tree(entries[0].parent, data/'loader')
    copy_tree(stage/'root', data/'cp')
    shutil.copy2(inputs.verification_tar, portable/'userdata'/'nuttymod_cube_verifycation.tar')
    shutil.copy2(inputs.root_tar, data/'cp'/'nuttymod_root.tar')
    for name in ('root_mode_runtime.py', 'root_mode_loader.py', 'rootmode_manifest.json'):
        for destination in (build, portable): shutil.copy2(stage/'rootmode'/name, destination/name)
    shutil.copy2(inputs.rootmode_tar, data/'cp'/'rootmode.tar')
    profile_path = portable/'cpe-flash-profile.json'
    profile = json.loads(profile_path.read_text(encoding='utf-8'))
    # This replaces the generic single-file hook, which cannot resolve a whole
    # loader package. Other explicitly selected startup scripts still work.
    profile['loader'] = None
    profile['verbose_python'] = True
    profile['full_rewrite'] = True
    profile['nuttymod_root'] = {'schema': 1, 'version': manifest['version'],
        'loader': 'userdata/nuttymod/loader/nuttymod_loader.py',
        'files': {p.relative_to(portable).as_posix(): digest(p) for folder in (data/'loader', data/'cp') for p in folder.rglob('*') if p.is_file()}}
    profile['nuttymod_root']['root_mode'] = {'version': '1', 'library': '1.2',
        'files': {name: digest(portable/name) for name in ('root_mode_runtime.py', 'root_mode_loader.py', 'rootmode_manifest.json')}}
    for root in (build, portable):
        (root/'cpe-flash-profile.json').write_text(json.dumps(profile, indent=2), encoding='utf-8')
    return 'NuttyMod Root ' + str(manifest['version'])
