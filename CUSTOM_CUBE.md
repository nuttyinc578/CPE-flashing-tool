# Custom Cube Beta / CPE Series 2 — Ortain

In flasher 1.2.8, open **05 Custom Cube**. Use **Browse** to fill any of the six slots with a trusted TAR. Check as many slots as you want to include in **Flash ZIP + Recompile**. Packages and their startup hooks are applied in slot order, 1 through 6. If two packages target the same game file, the build stops and names the conflict. Uncheck one or use packages with different filenames.

**Uncheck all** keeps all saved paths but selects no overlays. **Clear** unchecks one slot and removes its path; it doesn't delete the TAR. Paths are saved locally when you close the tool, but all boxes start unchecked on the next launch.

**Use bundled Custom Ortain TAR** checks its existing slot or puts it in the first empty slot without replacing another package. **Use CPE Series 2 — Ortain project** separately selects the bundled engine project. Configure the original portable ZIP, installed folder, game Python and userdata as before. Unlock first, enable Full rewrite, and close the game before installing the staged build.

## Build Mode

In flasher 1.2.9, click **Use bundled Build Mode TAR** on **05 Custom Cube**. It checks the Build Mode slot without changing other selections. Use **Flash ZIP + Recompile**, then install the staged build. You can also browse to `Custom-Cube-Beta-Build-Mode.tar` manually.

In solo play, click **Build Mode** or press **B**. Left-click to place a piece on the grid. Use **1** for blocks, **2** for balls and **3** for fixed beams. **R** rotates the beam, **Z** undoes the last placed piece, and **B** or **Esc** leaves the mode. **Clear** removes the pieces and beams with the rest of the sandbox. Pieces last for the current solo session; online and LAN play are unchanged.

The TAR contains Python **code**, not a Python installation. A working compiler with game dependencies is still required. It is not a standalone game or installer. The supplied TAR changes the window caption, gives spawned shapes a neon palette and adds a gentle pulse on spawning when Ortain is active. You can add rewritten game modules to make deeper changes.

## Package layout

`custom-cube.json` at the TAR root declares schema `1`, API `CubeBeta/1`, a name, version, and `files`: a JSON object mapping `python/<filename>` to each file's SHA-256. Optional `startup` points to one of the inventoried Python files defining `on_load(app, userdata)`.

`python/` contains root-level `.py`, `.png` or `.ico` files. An inventoried `python/cube_core.py`, for example, replaces that game module **in staging** before the full build. Loader, integrity, Root Mode runtime modules and build configuration remain managed by the flasher. CPE engine packages use the separate project selector. This is a source-overlay format, not an EXE decompiler.

Edit the supplied `custom_cube_template/python/` files and run `tools/Build-CustomCube.py` to regenerate the starter TAR with matching hashes. The generator also makes `CPE-Series-2-Ortain.zip`; unpack it and select its `cpe-series-2-ortain` folder to use the project separately. Hashes verify consistency, not authorship.

## Ortain engine

Ortain uses the existing Rephysics solver and CPE/1 interface. Fast-moving bodies receive bounded cyan IPE trails automatically. `engine.motion_trails = False` disables them. `engine.pulse(x, y, radius=220, strength=280)` pushes nearby bodies outward and emits purple particles; this is an API for custom game code, not a new keyboard shortcut. Values and particle counts are bounded; paused engines do not emit motion trails.

Ortain declares `loading_preset: ortain` in its project manifest. Its loading scene replaces the Halloween music-download scene; it does not download a new soundtrack. Required modified-file and unlocked-loader warnings still appear first.

Only compile and run trusted code. Python packages can change gameplay and execute code during build/startup. A bad custom game can fail after compilation. Keep original downloads and backups; use Restore backup to undo the installation. Compatibility with every third-party rewrite is not guaranteed.
