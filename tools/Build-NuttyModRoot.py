"""Generate matching readable NuttyMod Root archives, without legacy bytecode."""
import hashlib
import io
import json
import shutil
import tarfile
import zipfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
output = root/'release-download'/'NuttyMod-Root'
output.mkdir(parents=True, exist_ok=True)
version = '1.0.0'
loader = output/'nuttymod_loader.py'
shutil.copy2(root/'nuttymod_root_package'/'nuttymod_loader.py', loader)
bundle = output/'NuttyMod-Root-Loader.zip'
with zipfile.ZipFile(bundle, 'w', zipfile.ZIP_DEFLATED) as archive:
    for path in (root/'nuttymod_root_package').iterdir():
        if path.is_file(): archive.write(path, 'nuttymod_loader/'+path.name)


def json_tar(path, name, value):
    data = json.dumps(value, indent=2).encode('utf-8')
    with tarfile.open(path, 'w') as archive:
        member = tarfile.TarInfo(name); member.size = len(data); member.mtime = 0
        archive.addfile(member, io.BytesIO(data))


root_tar = output/'nuttymod_root.tar'
json_tar(root_tar, 'root_manifest.json', {'schema': 1, 'version': version, 'settings':
    {'schema': 1, 'game': {'theme': 'halloween', 'gravity': 900, 'title': 'The Cube Beta — NuttyMod Root'},
     'cpe': {'aspire_ip': '127.0.0.1', 'node_port': 4310, 'bridge_enabled': True}}})
rootmode = output/'rootmode.tar'
with tarfile.open(rootmode, 'w') as archive:
    for name in ('root_mode_runtime.py', 'root_mode_loader.py'):
        archive.add(root/name, arcname=name)
    data = json.dumps({'schema': 1, 'version': '1', 'library': '1.2', 'game_level_only': True}).encode('utf-8')
    member = tarfile.TarInfo('rootmode_manifest.json'); member.size = len(data)
    archive.addfile(member, io.BytesIO(data))
hashes = {}
for key, path in (('loader_py', loader), ('loader_zip', bundle), ('root_tar', root_tar), ('rootmode_tar', rootmode)):
    with path.open('rb') as stream: hashes[key] = hashlib.file_digest(stream, 'sha256').hexdigest()
json_tar(output/'nuttymod_cube_verifycation.tar', 'verification.json', {'schema': 1, 'version': version, 'sha256': hashes})
shutil.copy2(root/'NUTTYMOD_ROOT.md', output/'NUTTYMOD_ROOT.md')
with zipfile.ZipFile(root/'release-download'/'NuttyMod-Root-1.0.0-Packages.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
    for path in output.iterdir():
        if path.is_file(): archive.write(path, 'NuttyMod-Root/'+path.name)
print('NuttyMod Root packages created:', output)
