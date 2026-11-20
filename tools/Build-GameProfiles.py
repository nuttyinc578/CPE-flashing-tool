"""Pack only tracked free game build inputs from the exact release commits."""
import argparse
import hashlib
import io
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cpe_flasher.releases import PROFILE_REVISIONS

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--repository',type=Path,required=True)
    args=parser.parse_args()
    out=ROOT/'build/game-versions'
    out.mkdir(parents=True,exist_ok=True)
    legacy=ROOT/'build/flasher-source'
    music=(legacy/'fall_music.mp3').read_bytes()
    if hashlib.sha256(music).hexdigest()!='17b93051af84d00443ce32588bdf422e22f63306c7afd43712d4756e61baafe4':
        raise RuntimeError('Official fall_music.mp3 missing or mismatched in rebuild bundle.')
    for version,rev in PROFILE_REVISIONS.items():
        git=['git','-C',str(args.repository)]
        tracked=subprocess.check_output([*git,'ls-tree','--name-only',rev],text=True).splitlines()
        names=[n for n in tracked if not n.startswith(('test_','.')) and (
            Path(n).suffix in {'.py','.js','.rb','.ico','.png','.spec','.txt','.cmd'} or n in
            {'click.mp3','cpe-backend.json','nightly-config.json','cpe','cpe_rephysics','addons','themes','repair_payload','cube_launcher','archive_assets'})]
        source=zipfile.ZipFile(io.BytesIO(subprocess.check_output([*git,'archive','--format=zip',rev,'--',*names])))
        with zipfile.ZipFile(out/(version+'.zip'),'w',zipfile.ZIP_DEFLATED) as dest:
            for name in source.namelist():
                if name.endswith('/') or set(Path(name).parts)&{'bin','obj','__pycache__','tests','node_modules'}:continue
                if name.startswith('archive_assets/') and Path(name).suffix.lower() not in {'.png','.md'}:continue
                dest.writestr(name,source.read(name))
            dest.writestr('fall_music.mp3',music)
            if version=='6.4.1':
                for n in ('flashed_runtime.py','root_mode_runtime.py','root_mode_loader.py','nuttymod_root_support.py'):
                    if n not in source.namelist(): dest.write(legacy/n,n)
        print(f'Packed {version}: {rev}',flush=True)
if __name__=='__main__': main()
