from pathlib import Path

a = Analysis(['CPE Flasher Tool.py'], pathex=[], binaries=[],
             datas=[('icon.ico', '.'), ('build/flasher-source', '.')],
             hiddenimports=[], hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[])
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name='CPE Flasher Tool',
          console=False, icon='icon.ico', upx=False)
