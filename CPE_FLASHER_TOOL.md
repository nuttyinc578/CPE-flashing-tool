# CPE Flasher Tool

## Settings — custom portable ZIP

**06 Settings → Custom portable ZIP** enables unofficial compatible game ZIPs,
including NuttyMod runtime portable ZIPs. It is off at every launch. Select the
ZIP on tab 01 and paste its owner's **64-character SHA-256** into the custom SHA
field on tab 06. The flasher checks it before extraction or compilation and asks
for confirmation on enabling the setting and before each custom build.

Custom portable ZIPs may have any filename (for example `My NuttyMod build.zip`).
The game executable may also be renamed, including spaces or `.EXE`. Leave
the two optional EXE-name fields on tab 06 blank for automatic detection, or
enter the exact **filename only** for the EXE inside the ZIP and the installed
EXE. The installed-EXE Browse button selects its folder too. Detection prefers
the standard game filename, otherwise requires one top-level EXE; it never
guesses between multiple custom EXEs or selects helpers from subfolders.

The rebuilt custom ZIP keeps the selected EXE name and is named
`<input ZIP name>-Flashed.zip`. The game is rebuilt from matching source, not by
decompiling the input EXE. A custom build spec can emit a renamed top-level EXE
too. If the installed game had a different EXE name, its selected old EXE is
backed up and removed when replaced; the shortcut points to the new EXE.
Restore backup returns the previous EXE and shortcut. Standard mode retains the
official EXE name and all existing verification requirements.

**WARNING: Unofficial builds are a great SECURITY RISK.** They may run malicious
code, damage the game or access your files. A matching hash checks consistency,
not safety or authorship. Only use code and a checksum obtained from an owner you
trust. No antivirus scan, signature verification or sandbox is provided.

**Unofficial builds cannot use official in-game updates. Updates are provided by
the owner of the custom ZIP.** The rebuilt game enforces this even when the
unlocked-update bypass mod is selected or the loader is later relocked. This is
an application policy, not tamper-proof security or an automatic custom updater.
Obtain a replacement ZIP and its checksum from that owner, back up the game,
then repeat the normal unlock/rebuild workflow to install it.

Custom ZIPs still require CPELoader components, a valid integrity manifest,
complete matching source, userdata and initial unlock. Modified files are
accepted only in custom mode; the existing baseline is preserved so modification
warnings remain. Path/size/link checks, backups and restore stay enabled. For
NuttyMod Root, the custom SHA replaces the official portable checksum file only;
all loader/TAR package verification remains required. This does not make an
arbitrary ZIP compatible, and recompilation uses the source selected on tab 01
or bundled inside the selected ZIP, not the custom EXE itself.

## Undo and restore

Close the game before restoring. **Undo changes** restores the most recent flash
completed in the current flasher session; before installation it only discards
the prepared build (the installed game is untouched). **Restore backup…** lets
you select an earlier timestamped folder under the target game's
`backup/cpe-flasher/` containing `manifest.json`.

Restoration puts back overwritten/deleted files and removes files introduced by
that flash. It restores the recorded loader state and shortcut too. Unrelated
files and saves are not changed, but userdata files overwritten by the flash
are restored to their backed-up versions. A `before-restore-*` recovery backup
is created first and can be selected to undo a restore. Original backups remain.
Restore does not require a working or unlocked game. Missing backup files stop
restoration before replacement; a replacement failure rolls changes back.

A Windows GUI for flashing CPE Rephysics and compatible CPE projects into The
Cube Beta. No terminal commands are required in the app.

1. Open the current game, press Ctrl+A and Y to unlock CPELoader, then close it.
2. Start **CPE Flasher Tool.exe**. Choose an original Cube Beta portable ZIP.
3. Locate the installed game or browse to its folder.
4. Leave the project field blank for bundled Rephysics, select a separate
   Rephysics repository folder, or select a compatible custom project.
5. Choose an installed Python 3.12 interpreter with the packages in
   `requirements.txt`. The game's existing `.venv/Scripts/python.exe` works.
   The flasher cannot rebuild an EXE without a Python compiler environment.
6. Open the **Userdata / loaders / rewrite** tab. Choose a userdata folder or
   click **Create userdata folder**. `userdata.json` must contain `{"schema": 1}`.
   Userdata is required; custom loaders and scripts are optional.
7. Confirm that you trust the code, then click **Flash ZIP + Recompile**.
8. After compilation succeeds, click **Replace game + Create shortcut**.

The app first works in a separate staging folder under
`%LOCALAPPDATA%/CPEFlasherTool/staging`. It validates ZIP paths and the original
portable manifest, rebuilds the entire game using PyInstaller, and creates a
flashed portable ZIP. New portable downloads include `game-source.zip`.
For older ZIPs, use the bundled current game source or select matching source
manually. Historical executables without CPELoader are not supported.
Selected complete source takes priority over source inside the ZIP.

## Userdata, root and optional loaders

The startup corruption warning explains the required sequence. Game-level root
enables custom startup code; it does not grant Windows administrator access.
The flashed ZIP and installed game retain the unlocked state for all three
CPELoader components. Both integrity and 50% unlocked warnings remain mandatory.

Choose an optional trusted `.py` custom mod/add-on loader and additional `.py`
startup scripts. They are copied into `flash_scripts/` and run in that order.
They receive `app`, `userdata`, `game_root` and `logger` globals. An optional
`on_load(app, userdata)` function is called after the script executes. Scripts
must be self-contained or depend on modules available in the game; this is not
a sandbox or an automatic dependency installer.

VP enables a Python console with verbose import output plus startup/hook logs in
`userdata/verbose-python.log`. With VP off, the game keeps its normal windowed
launch. The Safety Cube option controls only a cosmetic custom-loader preference
(`app.safety_cube_alerts`); there is no separate built-in Safety Cube system to
remove. It never disables CPELoader warnings, backups or installation checks.

Full rewrite is enabled by default: complete selected source is staged, flashed,
compiled, and copied with the rebuilt executable into the portable and target
folders. Obsolete files listed in the original managed-file manifest are backed
up and removed; unknown files, backups and existing player settings are retained.
Selected userdata merges into the target (matching selected files are backed up
before replacement). Recompilation does not invent or decompile missing source.
The flashed ZIP contains the selected userdata. Do not select an unrelated
personal folder, and remove private information before sharing that ZIP.

Compilation failure leaves the installed game untouched. Replacement copies
previous files into `backup/cpe-flasher/<timestamp>/files` and records a manifest.
If replacement fails, already changed files are restored. Existing player
settings are preserved. The shortcut is created **after** replacement succeeds,
inside the installed game folder, and points to the rebuilt EXE.

Flashing keeps the original portable integrity manifest; it does not reseal or
silently approve the new game files. The rebuilt game displays a modified-file
warning and the existing unlocked-loader warning at 50% loading. Enter continues.
Repeatedly unlocking cannot hide changes from the original release manifest.

## Other CPE projects

Custom projects contain `cpe-project.json`:

```json
{"api": "CPE/1", "name": "My CPE engine", "version": "0.1"}
```

They also provide `cpe_project/__init__.py`, exporting `CubePhysicsEngine`, and
`cpe_project/physics.py`, exporting the Pymunk-compatible body, shape, vector and
space API used by `cube_core.py`. Engine instances implement the same methods as
`cpe_rephysics/engine.py`, including `register_body`, `execute_line`, `step`,
`snapshot`, `health_report`, particles and rendering. The compiler performs a
basic engine/API smoke check before rebuilding. That does not certify every
physics feature: compatible API behavior remains the project author's job.

Only use trusted source and projects: Python code can execute while compiling
and playing. CPELoader is an application-level gate, not tamper-proof security.
The flasher does not modify running processes, patch EXE bytes, install drivers,
or bypass the initial flashing lock. Backups remain available for manual recovery.

## NuttyMod — Bypass (v1.2.0)

The fourth tab offers the built-in **CPELoader unlock updates disabled bypass mod**.
Select it before Flash ZIP + Recompile, then confirm the warning. This sets an
explicit update-policy override in the managed `cpe-flash-profile.json`, compiles
the updated CPELoader into the EXE and replaces matching source sidecars.
It permits the existing in-game update/version/experience paths to run with a
valid unlocked loader. It does not add an updater where one does not exist.
Initial flashing still requires Ctrl+A → Y. Missing loader components and corrupt
unlock state do not activate the override. Integrity warnings and update/install
backups remain active. Updates may overwrite mods and remove this override;
keep the original ZIP and backup. To disable it, reflash with the checkbox cleared
or restore the prior backup. Other trusted `.py` loaders/scripts remain on tab 02.

## Python directory discovery

`flashing.patch` is a JSON discovery configuration (not a shell command or a
unified-diff patch). The app loads it directly and bundles it in the Windows EXE.
Select either `python.exe` or its installation/virtual-environment folder. Known
layouts include `Scripts/python.exe` and `.venv/Scripts/python.exe`. **Detect and
check Python** searches standalone installations and validates Python 3.11+
(3.12 recommended), Pygame, Pymunk and PyInstaller. Missing packages show a
compiler-specific installation instruction; the app does not install them silently.
It never defaults to the Python running Codex. Game discovery does not use the
current working directory; select the actual game folder if auto-detection fails.
