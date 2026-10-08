# NuttyMod Root 1.0.0

NuttyMod Root is **game-level customization under userdata**, not Windows root,
administrator access, a driver, or an operating-system security change.
It uses a new readable Python loader. The isolated legacy NuttyMod 1.4.2 files
are preserved; their old Python bytecode loader is not compatible with this flow.

## Files and flash order

1. Download an original Cube Beta portable ZIP **and SHA256SUMS.txt** from
   [the official game release](https://github.com/nuttyinc578/the-cube/releases).
   Use a release containing CPELoader. Do not use an already-flashed ZIP.
2. Open the installed game, Ctrl+A → Y to unlock, then close the game.
3. Open the updated CPE Flasher Tool. Choose the official ZIP, target folder,
   bundled current complete source and Python compiler in Game / compiler.
4. Create/select a userdata folder. Select the supplied **nuttymod_loader.py**
   in the custom loader input on Userdata / loaders / rewrite.
5. On NuttyMod Root, enable **Flash NuttyMod Root**. Put
   **NuttyMod-Root-Loader.zip** into the loader-folder ZIP input. This is the
   complete matching loader folder, not a single Python file renamed ZIP.
6. Put **nuttymod_root.tar** into the **CP** input. Here CP means the Root
   configuration/package payload, not a different physics backend.
7. Put **nuttymod_cube_verifycation.tar** into the **Userdata** verification input.
   The spelling matches the requested filename. Select the official checksum file.
   Also select **rootmode.tar** in Required Root Mode library. This library is
   mandatory: Root Mode v1 / library v1.2. Keep **Full rewrite** enabled.
8. Trust the packages, Flash ZIP + Recompile, wait for success, then confirm
   Replace game + Create shortcut. Backups remain in backup/cpe-flasher.

Packages must belong to the same generated set. Checksums detect mismatched or
changed bytes; they are not digital signatures and cannot establish the source
of an untrusted checksum file. Obtain the official ZIP/checksums from the trusted
release page. Custom Python remains trusted code and can change the game.

## Installed layout and settings

The entire loader folder is copied to `userdata/nuttymod/loader/`. The Root TAR
and its extracted manifest are under `userdata/nuttymod/cp/`. The verification
TAR is stored at `userdata/nuttymod_cube_verifycation.tar`. The flash profile
outside userdata records immutable loader/CP file hashes, checked before loading.
If these files change unexpectedly, Root is disabled and the game shows a
CPELoader warning; it does not silently execute the modified package.

SETTINGS, or **Ctrl+Shift+R**, opens NuttyMod Root Settings. Change theme, gravity,
window title, Aspire IP/hostname, Node.js port, or bridge on/off. Preferences are
saved to `userdata/nuttymod/settings.json`. Bridge changes affect the next Play
session. The base game settings remain accessible. Switching the compiled CPE
backend or game source still requires another flash/rebuild.

Root Mode adds music, click sounds, event frequency (6–120 seconds), and a VP
loading-record toggle. The left corner displays `root mode v1`, `root mode lib
v1.2`, and `nuttymod root v1`. VP loading records are stored locally in
`userdata/nuttymod/vp-loading.log`; no logs are uploaded. The Python compiler's
verbose/import console is enabled by this flash and changing it requires a rebuild.

The flasher installs the Root Mode loader, runtime, and manifest into the core
game files, compiles those modules into the executable, and copies the library
TAR into userdata. Core file hashes are verified before the custom loader runs.
Root Mode provides confined userdata file access, not unrestricted OS access.
Required integrity/unlock warnings cannot be switched off in Root settings.
Use all files from the newly generated package set together; older verification
TARs do not match the new required library.

The flashed ZIP and target folder stay unlocked, with CPELoader warnings and
installer-only updates. This does not auto-enable legacy NuttyMod patches, Fun
Mode or Physics3D. Those add-ons remain isolated until explicitly loaded.
The output ZIP contains userdata: remove private information before sharing.

Build matching local packages with `tools/Build-NuttyModRoot.py`. This does not
publish anything to GitHub or flash an installed game.
