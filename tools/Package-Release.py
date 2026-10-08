"""Package the tested executable and integrated game rebuild source."""
import argparse
import hashlib
import shutil
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
from cpe_flasher.core import pack_source
parser = argparse.ArgumentParser()
parser.add_argument('--game-repo', type=Path, required=True)
args = parser.parse_args()
game = args.game_repo.resolve()
output = root/'release-download'
output.mkdir(exist_ok=True)
shutil.copy2(game/'dist'/'CPE Flasher Tool.exe', output/'CPE-Flasher-Tool-1.0.0-Windows.exe')
shutil.copy2(game/'release-download'/'NuttyMod-Root-1.0.0-Packages.zip', output/'NuttyMod-Root-1.0.0-Packages.zip')
pack_source(game/'build'/'flasher-source', output/'Cube-Beta-Rebuild-Source-1.0.0.zip')
files = [output/'CPE-Flasher-Tool-1.0.0-Windows.exe', output/'NuttyMod-Root-1.0.0-Packages.zip', output/'Cube-Beta-Rebuild-Source-1.0.0.zip']
lines = []
for path in files:
    with path.open('rb') as stream: checksum = hashlib.file_digest(stream, 'sha256').hexdigest()
    lines.append(checksum+'  '+path.name)
(output/'SHA256SUMS.txt').write_text('\n'.join(lines)+'\n', encoding='utf-8')
print('\n'.join(lines))
