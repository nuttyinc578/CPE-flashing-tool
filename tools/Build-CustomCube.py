"""Create deterministic Custom Cube TARs and the shareable Ortain project ZIP."""
import hashlib
import io
import json
import tarfile
import zipfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
output = root/'release-download'; output.mkdir(exist_ok=True)
def build_tar(template, filename, title, startup):
    folder = root/template
    files = {p.relative_to(folder).as_posix(): p.read_bytes() for p in sorted((folder/'python').glob('*.py'))}
    manifest = {'schema':1, 'api':'CubeBeta/1', 'name':title, 'version':'1.0.0',
                'startup':startup, 'files':{n:hashlib.sha256(b).hexdigest() for n,b in files.items()}}
    files['custom-cube.json'] = json.dumps(manifest, indent=2).encode()
    with tarfile.open(output/filename, 'w') as archive:
        for name, data in sorted(files.items()):
            info = tarfile.TarInfo(name); info.size = len(data); info.mode = 0o644
            archive.addfile(info, io.BytesIO(data))
    print(output/filename)


build_tar('custom_cube_template', 'Custom-Cube-Beta-Ortain.tar', 'Custom Ortain Edition', 'python/custom_cube.py')
build_tar('build_mode_template', 'Custom-Cube-Beta-Build-Mode.tar', 'Cube Beta Build Mode', 'python/cube_build_mode.py')

with zipfile.ZipFile(output/'CPE-Series-2-Ortain.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
    project = root/'projects'/'cpe-series-2-ortain'
    for path in sorted(project.rglob('*')):
        if path.is_file() and '__pycache__' not in path.parts:
            info = zipfile.ZipInfo('cpe-series-2-ortain/'+path.relative_to(project).as_posix())
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, path.read_bytes())
print(output/'CPE-Series-2-Ortain.zip')
