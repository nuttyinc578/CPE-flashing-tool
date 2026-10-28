# CPE Flasher Tool v1.2.3 — Custom menus and older portable ZIPs

## New settings

- **Allow custom code, menus and files** preserves extra compatible source folders and assets through staging, rebuilding, installation and source ZIP repacking. It requires custom ZIP mode, Full rewrite and explicit confirmation. Accepting it clears the default bundled-source selection so the custom ZIP can supply its complete source; deliberately selected matching external source is retained.
- **Remove old portable ZIP restrictions** enables experimental import of older input ZIPs that lack current CPELoader sidecars or have a missing/obsolete integrity manifest. It requires custom ZIP mode and Full rewrite. If several EXEs are present, enter the exact game EXE filename on tab 06; helpers are not guessed.
- Both settings are **off at every launch**, have warnings and require confirmation again before building. Compatible renamed game EXEs and ZIP filenames remain supported.

## Important limits and warnings

Custom ZIPs are great for custom menus and files, but untrusted code is a serious **SECURITY RISK**: it can access/change your files, steal information or corrupt the game while compiling or playing. A matching SHA-256 checks consistency, not safety or authorship. This tool is not a sandbox. Review source, userdata and the output ZIP before sharing; skipping common private source files is not complete secret detection.

Old ZIP compatibility relaxes **input ZIP checks only**. You still need a trusted ZIP SHA-256, compatible complete rebuild source, userdata, a working Python 3.11+ compiler with Pygame/Pymunk/PyInstaller, and an unlocked current game installation with its existing valid integrity baseline. The current target's original baseline is retained instead of inventing a trusted seal for old files.

This does **not** decompile an EXE, reconstruct a historical game version, automatically activate copied menu files, or make an old installed game without CPELoader flashable. Custom source must connect its menu to the game; its PyInstaller spec must include required data and dynamic imports. Incompatible older files may corrupt the game.

Archive path/link/size protections, target unlocking, managed loader policy, modification warnings, backups and restore remain enabled. Unofficial builds cannot use official in-game updates, even with the update-bypass mod; updates are provided by their ZIP owner. Close the game before replacing or restoring files. Windows executables are unsigned and may trigger SmartScreen.

## Downloads and verification

- `CPE-Flasher-Tool-1.2.3-Windows.exe`: the flasher application, **not** the game portable ZIP. Bundles base rebuild source, Custom Ortain TAR and Ortain project.
- `NuttyMod-Root-1.0.0-Packages.zip`: matching Root Mode loader/library/TAR set generated together.
- `Custom-Cube-Beta-Ortain.tar` and `CPE-Series-2-Ortain.zip`: editable starter package and project source.
- `Cube-Beta-Rebuild-Source-1.0.0.zip`: checksum-pinned base source; managed overlays are applied during rebuilding. Use matching custom source where needed.
- `flashing.patch`: Python discovery configuration.
- `SHA256SUMS.txt`: checksums for the Windows EXE and four archives.

The local feature build passed all 79 regressions and its compiled startup check. The release Windows workflow also runs the full suite and verifies version 1.2.3, six tabs, bundled rebuild inputs and disabled-by-default experimental settings before packaging downloads.

See the [flashing guide](https://github.com/nuttyinc578/CPE-flashing-tool/blob/v1.2.3/CPE_FLASHER_TOOL.md) and [changelog](https://github.com/nuttyinc578/CPE-flashing-tool/blob/v1.2.3/CHANGELOG.md).
