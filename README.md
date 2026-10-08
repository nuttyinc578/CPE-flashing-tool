# CPE Flasher Tool

Windows desktop tool for flashing CPE Rephysics, compatible third-party CPE
projects, and NuttyMod Root into The Cube Beta. It rebuilds the complete game
before replacing the installation, creates backups, and then creates a shortcut.

[Download the Windows app](https://github.com/nuttyinc578/CPE-flashing-tool/releases/latest)
· [Flashing guide](CPE_FLASHER_TOOL.md) · [NuttyMod Root guide](NUTTYMOD_ROOT.md)

[Visit the website](https://nuttyinc578.github.io/CPE-flashing-tool/)

v1.1.0 adds a refreshed desktop interface with scrollable setup panels, a live
activity sidebar, clear install/recovery actions, and matching GitHub Pages.

## Included

- Portable ZIP selection, game location/browse, and a Python compiler selector.
- Required userdata; optional trusted Python loaders and startup scripts.
- Full managed-source rewrite/recompile, CPELoader warnings, and installer-only updates.
- NuttyMod Root v1 with required Root Mode v1 / library v1.2, game/CPE settings,
  version overlay, and local VP loading logs.
- **Undo changes** reverses the last flash in this session, or discards an
  uninstalled build. **Restore backup** selects an earlier backup, with a
  pre-restore recovery snapshot and preservation of unrelated saves.

## Before flashing

Keep an original official Cube Beta portable ZIP and its SHA256SUMS.txt. Unlock
CPELoader in the game with Ctrl+A → Y, then close the game. Choose a Python 3.11+
interpreter with pygame, pymunk and PyInstaller installed. Only flash code you
trust: compiling and loading custom Python executes that code. Incorrect flashing
can corrupt the game. Backups are under `backup/cpe-flasher/`.

Root Mode is game-level customization, **not Windows administrator/root access**.
It cannot switch off required integrity warnings. The flashed ZIP includes
userdata: remove private information before sharing. Logs stay local; this
flasher does not upload userdata or logs.

The release app bundles current complete game rebuild source. Use all Root
TAR/loader files from the same package set and enable Full rewrite. Use an
original official portable ZIP, not a previously flashed ZIP.

## Build from source

Use Windows and Python 3.12. Download `Cube-Beta-Rebuild-Source-1.0.0.zip` and
`SHA256SUMS.txt` from this repository's v1.0.0 release. Verify the source ZIP
against that checksum file, then run:

```powershell
python -m pip install -r requirements.txt
python -m unittest test_flasher_restore -v
python tools/Build-Flasher.py --game-source Cube-Beta-Rebuild-Source-1.0.0.zip --sha256 <source-zip-sha256>
python tools/Build-NuttyModRoot.py
```

The executable is `dist/CPE Flasher Tool.exe`. The source ZIP is integrated game
build input, not player data; it includes licenses and third-party notices.
The Actions workflow builds a downloadable Windows artifact. Executables,
archives, personal userdata, loader state, caches and backups are excluded from Git.

MIT source: [LICENSE](LICENSE). Assets and third-party components retain their
own licenses: [THIRD_PARTY_NOTICES.txt](THIRD_PARTY_NOTICES.txt).
