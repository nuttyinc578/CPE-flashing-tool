"""Package interface v1.1.1 without changing the pinned game-source release."""
import hashlib
import shutil
import argparse
from pathlib import Path

root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--app', type=Path, default=root/'dist'/'CPE Flasher Tool.exe')
args=parser.parse_args()
output=root/'release-download'; output.mkdir(exist_ok=True)
app=output/'CPE-Flasher-Tool-1.1.1-Windows.exe'
shutil.copy2(args.app, app)
files=[app, output/'NuttyMod-Root-1.0.0-Packages.zip', output/'Cube-Beta-Rebuild-Source-1.0.0.zip']
lines=[]
for path in files:
    with path.open('rb') as stream: checksum=hashlib.file_digest(stream,'sha256').hexdigest()
    lines.append(checksum+'  '+path.name)
(output/'SHA256SUMS.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('\n'.join(lines))
