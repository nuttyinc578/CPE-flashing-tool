# CPE Flasher Tool v1.2.2 — Custom portable builds

## New

- **06 Settings → Custom portable ZIP** accepts compatible unofficial and NuttyMod runtime portable ZIPs with an owner-provided, 64-character SHA-256. It is off at launch, asks for confirmation, and checks the hash before extraction or compilation.
- Custom game EXE and ZIP filenames work, including spaces and `.EXE`. Optional fields specify the EXE inside the ZIP and the installed EXE; automatic detection never guesses between multiple custom EXEs or selects helpers from subfolders.
- Rebuilt custom ZIPs keep their selected EXE name and use `<input ZIP name>-Flashed.zip`. Shortcuts target that EXE. A differently named previous game EXE is backed up before replacement; restore recovers it and the previous shortcut.
- Custom NuttyMod Root builds use the custom ZIP checksum instead of the official portable checksum file. Loader/TAR package verification remains mandatory.
- Unofficial builds block **official in-game updates**, even with the unlocked-update bypass selected or after relocking. Updates are provided by the owner of the custom ZIP; no automatic custom update service is added.

## Warning and requirements

**WARNING: Unofficial builds are a great SECURITY RISK. This includes NuttyMod runtime portable ZIPs.** They may run malicious code, damage the game or access your files. A matching hash proves consistency, not safety or authorship. Only use trusted code and checksums from an owner you trust.

Still required: a compatible Cube Beta portable with CPELoader and a valid integrity manifest, complete matching game source, userdata, an unlocked installed game, and Python 3.11+ with Pygame, Pymunk and PyInstaller for rebuilding. Select matching source on tab 01, or clear that field to use source bundled inside the selected ZIP. An EXE alone cannot be recompiled or decompiled by this tool.

Archive safety checks, modification warnings, backups and restore stay enabled. Close the game before replacing/restoring files. Root is game customization, not Windows administrator access. Custom builds and third-party rewrites are not guaranteed compatible. Windows executables are unsigned and may trigger SmartScreen.

## Downloads

- `CPE-Flasher-Tool-1.2.2-Windows.exe`: the flasher application, not the game portable ZIP. Includes the rebuild source, Custom Ortain TAR and Ortain project.
- `NuttyMod-Root-1.0.0-Packages.zip`: matching Root Mode library/loader/TAR set generated together.
- `Custom-Cube-Beta-Ortain.tar` and `CPE-Series-2-Ortain.zip`: editable starter package and project source.
- `Cube-Beta-Rebuild-Source-1.0.0.zip`: the checksum-pinned base game source; current managed overlays are integrated by the flasher.
- `flashing.patch`: Python discovery configuration.
- `SHA256SUMS.txt`: SHA-256 checksums for the EXE and four archives.

The previous local feature build passed 56 tests and its compiled startup self-test. This release's Windows workflow also runs those regressions and checks version 1.2.2, six tabs, safe defaults and bundled rebuild inputs before packaging downloads.

See the [flashing guide](https://github.com/nuttyinc578/CPE-flashing-tool/blob/v1.2.2/CPE_FLASHER_TOOL.md) and [changelog](https://github.com/nuttyinc578/CPE-flashing-tool/blob/v1.2.2/CHANGELOG.md).
