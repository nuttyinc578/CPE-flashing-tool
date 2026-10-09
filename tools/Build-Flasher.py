"""Build a Windows flasher with a checksum-verified complete game-source ZIP."""
import argparse
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
from cpe_flasher.core import safe_extract, source_root
parser = argparse.ArgumentParser()
parser.add_argument('--game-source', type=Path, required=True)
parser.add_argument('--sha256', required=True)
args = parser.parse_args()
with args.game_source.open('rb') as stream:
    actual = hashlib.file_digest(stream, 'sha256').hexdigest()
if actual != args.sha256.lower(): raise SystemExit('Game source ZIP checksum mismatch.')
stage = root/'build'/'flasher-source'
if stage.exists():
    if not stage.resolve().is_relative_to(root/'build'): raise SystemExit('Unsafe staging path.')
    shutil.rmtree(stage)
safe_extract(args.game_source, stage)
source_root(stage)
# The release ZIP pins the base game; Root support evolves with this repository.
shutil.copy2(root/'nuttymod_root_support.py', stage/'nuttymod_root_support.py')
subprocess.run([sys.executable, '-m', 'PyInstaller', '--noconfirm', 'cpe_flasher_build.spec'], cwd=root, check=True)
