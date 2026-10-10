# CPE Flasher Tool v1.2.1 — Custom Cube Beta and CPE Series 2 Ortain

## New

- **05 Custom Cube** accepts a trusted `.tar` containing Python game overlays and an optional startup hook. Packages are checked in staging and applied before the full game rebuild.
- Bundled **Custom Ortain Edition** TAR: neon shape colors, a custom window caption, and gentle spawn pulses when Ortain is active. Editable Python can also overlay game modules such as `cube_core.py`.
- Bundled **CPE Series 2 — Ortain 2.0.0** project extends the CPE Rephysics solver with bounded cyan motion trails, a radial `pulse(x, y)` API, and project metadata.
- Ortain's animated cyan/purple loading screen runs after mandatory integrity and unlocked-loader prompts. Other projects keep the Halloween scene. No new soundtrack is downloaded.
- New changelog and Custom Cube package guide; matching TAR and standalone project ZIP are downloadable below.

## How to use

Download the Windows app and open **05 Custom Cube**. Choose **Use bundled Custom Ortain TAR** and **Use CPE Series 2 — Ortain project**, or select your own compatible trusted package/project. Configure an original official game portable ZIP, installed game folder, Python compiler and userdata. Unlock CPELoader first, enable Full rewrite, then Flash ZIP + Recompile and confirm installation with the game closed.

The TAR contains Python code, **not a Python installation**. A working Python 3.11+ compiler with Pygame, Pymunk and PyInstaller is still required. This download is the flasher, not the game portable ZIP. The separate Ortain ZIP is source: unpack it and select its project folder in the flasher.

## Safety and recovery

Only compile trusted code. Package hashes check consistency, not authorship. Python game rewrites can fail or behave differently after compilation. Initial unlocking, userdata, full rebuild, modification warnings and backup/recovery controls remain active. Keep your original game ZIP and backups; Restore backup can undo an installation. Loader/integrity modules remain managed, and this is not Windows administrator/root access or a sandbox for untrusted mods. Compatibility with all third-party rewrites is not guaranteed.

## Downloads and verification

- `CPE-Flasher-Tool-1.2.1-Windows.exe`: app with the starter TAR, Ortain project and game rebuild source bundled.
- `Custom-Cube-Beta-Ortain.tar`: editable Custom Cube package.
- `CPE-Series-2-Ortain.zip`: standalone Ortain project source, including its MIT license.
- `NuttyMod-Root-1.0.0-Packages.zip` and `Cube-Beta-Rebuild-Source-1.0.0.zip`: unchanged Root package set and pinned base source. Current loader/UI overlays are integrated by the flasher during builds.
- `flashing.patch`: Python discovery configuration retained from v1.2.0.
- `SHA256SUMS.txt`: checksums for the Windows app and the four package/source archives.

20 local feature/recovery tests passed. Both the Windows flasher and the actual game compiled successfully with the supplied Ortain project and Custom Cube TAR. The compiled flasher self-test verified all five tabs and bundled files.

See [changelog](https://github.com/nuttyinc578/CPE-flashing-tool/blob/main/CHANGELOG.md) and [Custom Cube guide](https://github.com/nuttyinc578/CPE-flashing-tool/blob/main/CUSTOM_CUBE.md).
