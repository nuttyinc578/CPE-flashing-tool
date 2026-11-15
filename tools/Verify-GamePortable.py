"""Exercise a trusted release portable against a disposable copy, never a real installation."""
import argparse
import hashlib
import sys
import tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from cpeloader import CPELoader, write_json
from cpe_flasher.core import FlashOptions, compile_game, find_portable, prepare_flash, safe_extract, select_executable
from cpe_flasher.releases import exe_version, source_version

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('archive',type=Path)
    ap.add_argument('--compile',action='store_true',help='Also run the actual PyInstaller game compiler')
    args=ap.parse_args()
    archive=args.archive.resolve()
    hashes={name.lstrip('*'):digest.lower() for digest,name in (line.split(maxsplit=1) for line in archive.with_name('SHA256SUMS.txt').read_text(encoding='utf-8-sig').splitlines() if line.strip())}
    with archive.open('rb') as src: assert hashlib.file_digest(src,'sha256').hexdigest()==hashes[archive.name]
    with tempfile.TemporaryDirectory(prefix='flash-qa-',dir=ROOT/'build') as tmp:
        root=Path(tmp);safe_extract(archive,root/'original');game=find_portable(root/'original')
        exe=game/select_executable(game);version=exe_version(exe)
        manifest=(game/'cpeloader_manifest.json').read_bytes()
        CPELoader(game).unlock()
        user=root/'user';user.mkdir();write_json(user/'userdata.json',{'schema':1,'player_name':'QA'})
        def compiler(build,python,log):
            assert source_version(build)==version
            if args.compile:return compile_game(build,python,log)
            return exe  # Only when checking the archive/profile workflow without a full compiler run.
        plan=prepare_flash(archive,game,root/'stage',None,None,Path(sys.executable),print,compiler,FlashOptions(user))
        assert plan.executable_name==exe.name and exe_version(plan.portable/exe.name)==version
        assert (plan.portable/'cpeloader_manifest.json').read_bytes()==manifest
        assert (game/'cpeloader_manifest.json').read_bytes()==manifest
        assert CPELoader(plan.portable).unlocked and plan.output_zip.is_file()
        if (game/'cpe.exe').is_file():
            assert (game/'cpe.exe').stat().st_size==(plan.portable/'cpe.exe').stat().st_size
        print('Verified',version,'including game compilation' if args.compile else '(archive + matching build inputs; no game compilation)',flush=True)
if __name__=='__main__':main()
