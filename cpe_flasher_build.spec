from pathlib import Path

a = Analysis(['CPE Flasher Tool.py'], pathex=[], binaries=[],
             datas=[('icon.ico', '.'), ('build/flasher-source', '.'), ('flashing.patch', '.'),
                    ('game_overrides/cpeloader_ui.py', 'game_overrides'),
                    ('game_overrides/halloween_update.py', 'game_overrides'),
                    ('game_overrides/custom_cube_loading.py', 'game_overrides'),
                    ('projects/cpe-series-2-ortain/cpe-project.json', 'projects/cpe-series-2-ortain'),
                    ('projects/cpe-series-2-ortain/cpe_project/*.py', 'projects/cpe-series-2-ortain/cpe_project'),
                    ('release-download/Custom-Cube-Beta-Ortain.tar', '.')],
             hiddenimports=[], hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[])
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name='CPE Flasher Tool',
          console=False, icon='icon.ico', upx=False)
