# Changelog

## 1.2.3

- Optional **Remove old portable ZIP restrictions** allows experimental import of input ZIPs without today's loader sidecars/integrity format. It keeps the current target's original baseline, uses compatible modern rebuild source, and retains unlock, hash, archive-safety, warning and backup requirements.
- Optional **Allow custom code, menus and files** under tab 06 preserves additional compatible source folders/assets through rebuilding, portable ZIP creation and source repacking.
- Explicit benefit/security warning and per-build confirmation; requires custom ZIP mode, owner SHA-256, matching complete source and Full rewrite. Managed loader policy, update block, archive checks and backup/restore remain on.
- Clear the default bundled source on accepting this mode so custom ZIP source is not silently replaced. Common private source files, machine state, caches and backups are skipped; output must still be reviewed before sharing.

## 1.2.2

- Renamed custom portable ZIPs and game EXEs now work through discovery, rebuilding, replacement, backup/restore and shortcut creation. Optional exact-name fields resolve multiple-EXE ambiguity; custom output ZIPs keep the input ZIP stem.
- New **06 Settings** tab with opt-in **Custom portable ZIP**, including NuttyMod runtime builds, owner-supplied SHA-256 text, and explicit unofficial-build security warnings.
- Verify the custom ZIP hash before extraction/rebuild; keep integrity warnings, initial unlock, safe archive handling, backups and restore.
- Custom builds block official in-game updates even with the update-bypass mod; their ZIP owner provides updates. NuttyMod Root retains package verification while allowing the custom ZIP hash instead of an official portable checksum file.

## 1.2.1

- New **05 Custom Cube** tab accepts a trusted `.tar` with Python game overlays.
- Bundled Custom Ortain TAR with neon shapes and gentle spawn pulses through editable startup Python; full source overlays can replace game modules such as `cube_core.py` before recompilation.
- Manifest inventory, SHA-256 consistency checks and Python syntax checks happen in staging. Initial unlock, userdata, Full rewrite, backups and modification warnings remain required.
- New **CPE Series 2 — Ortain 2.0.0**, extending CPE Rephysics's independent solver: bounded cyan motion trails, the radial `pulse(x, y)` API and project metadata.
- Cyan/purple animated loading screen for Ortain, shown after mandatory integrity and unlocked-loader prompts. Other projects keep the Halloween loading screen.
- Matching TAR/project ZIP included in local downloads and future GitHub build artifacts.

## 1.2.0

- NuttyMod Bypass tab with an optional unlocked-update policy override.
- Trusted Python mod selection, Python/venv directory detection and dependency checks.
- `flashing.patch` discovery configuration; modified-file warnings and backups preserved.

## 1.1.1

- NuttyMod Root settings link to the existing Security / OG menu.

## 1.1.0

- Refreshed desktop interface and GitHub Pages site.

## 1.0.0

- Managed game rebuild, NuttyMod Root / Root Mode and backup recovery.
