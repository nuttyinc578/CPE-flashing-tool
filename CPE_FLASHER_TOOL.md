# CPE Flasher Tool

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
or bypass the loader lock. Backups remain available for manual recovery.
