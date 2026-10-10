"""Create a deterministic Custom Cube TAR and shareable Ortain project ZIP."""
import hashlib
import io
import json
import tarfile
import zipfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
output = root/'release-download'; output.mkdir(exist_ok=True)
files = {p.relative_to(root/'custom_cube_template').as_posix(): p.read_bytes()
         for p in (root/'custom_cube_template'/'python').glob('*.py')}
manifest = {'schema':1, 'api':'CubeBeta/1', 'name':'Custom Ortain Edition', 'version':'1.0.0',
            'startup':'python/custom_cube.py', 'files':{n:hashlib.sha256(b).hexdigest() for n,b in files.items()}}
files['custom-cube.json'] = json.dumps(manifest, indent=2).encode()
with tarfile.open(output/'Custom-Cube-Beta-Ortain.tar', 'w') as archive:
    for name, data in sorted(files.items()):
        info = tarfile.TarInfo(name); info.size = len(data); info.mode = 0o644
        archive.addfile(info, io.BytesIO(data))
with zipfile.ZipFile(output/'CPE-Series-2-Ortain.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
    project = root/'projects'/'cpe-series-2-ortain'
    for path in sorted(project.rglob('*')):
        if path.is_file() and '__pycache__' not in path.parts:
            info = zipfile.ZipInfo('cpe-series-2-ortain/'+path.relative_to(project).as_posix())
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, path.read_bytes())
print(output/'Custom-Cube-Beta-Ortain.tar')
print(output/'CPE-Series-2-Ortain.zip')
