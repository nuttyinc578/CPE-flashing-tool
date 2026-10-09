# CPE Flasher Tool v1.2.0 — NuttyMod Bypass and Python Discovery

## New

- **04 NuttyMod Bypass** includes the built-in **CPELoader unlock updates disabled bypass mod**. It is off by default. Enable it before Flash ZIP + Recompile, confirm the warning, then install the rebuilt game.
- Select trusted NuttyMod `.py` startup mods directly from that tab. Other loaders remain available under Userdata & loaders. Unsupported mods are not automatically made compatible.
- Select a Python executable **or its installation/virtual-environment folder**. `flashing.patch` supplies the directory discovery layouts and is bundled into the app.
- Detect and check Python validates Python 3.11+ and Pygame, Pymunk, PyInstaller. Missing dependencies show instructions for the selected interpreter. Codex runtime paths are excluded as compiler selections; game discovery no longer relies on the current working directory.
- The flashed game's loading warnings show whether the update override is enabled.

## Important

This is the **flasher**, not The Cube Beta portable game ZIP. Initial flashing still requires unlocking CPELoader with Ctrl+A → Y. Integrity warnings, the 50% acknowledgement, backups, Undo changes and Restore backup remain active. Corrupt state or missing loader components do not enable the override. In-game updates can overwrite your mods: keep an official original ZIP and backups. Reflash with the checkbox cleared or restore the earlier backup to remove the override.

The bypass is an explicit application update-policy option. It does not grant Windows administrator access, patch running processes or unlock unrelated systems. Only flash trusted source and mods. Userdata is included in flashed ZIPs; remove private information before sharing.

## Downloads

- `CPE-Flasher-Tool-1.2.0-Windows.exe`: Windows application, with complete pinned game source plus current loader/UI overlays integrated.
- `NuttyMod-Root-1.0.0-Packages.zip`: matching Root Mode package set (unchanged).
- `Cube-Beta-Rebuild-Source-1.0.0.zip`: pinned base game source (unchanged; the flasher applies current owned loader/UI overlays during rebuilding).
- `flashing.patch`: JSON discovery configuration, not an executable or a unified-diff patch.
- `SHA256SUMS.txt`: checksums for the application and two source/package archives.

52 local regression tests passed, along with the compiled Windows application's four-tab/source/configuration self-test and minimum-size layout check.
