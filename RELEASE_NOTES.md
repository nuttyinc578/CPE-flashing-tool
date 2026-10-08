# CPE Flasher Tool v1.0.0

First Windows release of the standalone CPE Flasher Tool.

- Flash compatible CPE projects or CPE Rephysics into an official Cube Beta portable ZIP.
- Full managed-code rewrite and Python/PyInstaller game recompilation before installation.
- Required userdata, optional trusted Python loaders/scripts, and verbose Python support.
- NuttyMod Root v1 and required Root Mode v1 / library v1.2, game/CPE configuration,
  corner version overlay, and local VP loading records.
- Undo changes and Restore backup, including a recovery snapshot before restoration.
- CPELoader unlock/integrity warnings and backup/rollback protections remain enabled.

Download **CPE-Flasher-Tool-1.0.0-Windows.exe** to run the tool. Download the
**NuttyMod-Root-1.0.0-Packages.zip** for all matching loaders and TARs, including
rootmode.tar. **Cube-Beta-Rebuild-Source-1.0.0.zip** is optional integrated game
build source (also bundled in the executable), not a playable game portable ZIP.
SHA256SUMS.txt covers all three release files. Download the original official
game portable ZIP and its checksum file from nuttyinc578/the-cube separately.

**Warning:** close the game, unlock CPELoader first, keep backups, and only
compile trusted code. Incorrect flashing can corrupt the installation. Root
means game customization, not Windows administrator access. Read the guides
before flashing. Personal userdata and local logs are not included in this release.
