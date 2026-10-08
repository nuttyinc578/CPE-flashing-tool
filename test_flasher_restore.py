import unittest
from unittest.mock import patch

import test_cpe_flasher as fixture
from cpe_flasher.core import EXE, FlasherError, install_flash, restore_backup
from cpeloader import CPELoader


class RestoreTests(unittest.TestCase):
    def setUp(self):
        self.f = fixture.FlasherTests(); self.f.setUp()
        CPELoader(self.f.target).unlock()

    def tearDown(self): self.f.tearDown()

    def install(self):
        self.plan = self.f.prepare()
        (self.plan.portable/'added.py').write_text('# flashed code')
        return install_flash(self.plan, lambda message: None,
                             lambda target, path: path.write_bytes(b'new shortcut'))

    def test_restore_original_files_remove_flash_additions_preserve_unrelated_saves(self):
        backup = self.install()
        saves = self.f.target/'userdata'/'new-save.json'; saves.write_text('{"score":42}')
        recovery = restore_backup(self.f.target, backup, lambda message: None)
        self.assertEqual((self.f.target/EXE).read_bytes(), b'original game')
        self.assertFalse((self.f.target/'added.py').exists())
        self.assertFalse((self.f.target/'The Cube Beta.lnk').exists())
        self.assertEqual(saves.read_text(), '{"score":42}')
        self.assertTrue((recovery/'manifest.json').is_file())
        self.assertTrue((backup/'manifest.json').is_file())

    def test_recovery_snapshot_can_undo_a_restore(self):
        (self.f.target/'The Cube Beta.lnk').write_bytes(b'old shortcut')
        backup = self.install()
        recovery = restore_backup(self.f.target, backup, lambda message: None)
        self.assertEqual((self.f.target/'The Cube Beta.lnk').read_bytes(), b'old shortcut')
        restore_backup(self.f.target, recovery, lambda message: None)
        self.assertEqual((self.f.target/EXE).read_bytes(), b'rebuilt game for Rephysics')
        self.assertTrue((self.f.target/'added.py').exists())

    def test_missing_backup_file_leaves_game_untouched(self):
        backup = self.install()
        (backup/'files'/EXE).unlink()
        with self.assertRaises(FlasherError): restore_backup(self.f.target, backup)
        self.assertEqual((self.f.target/EXE).read_bytes(), b'rebuilt game for Rephysics')

    def test_file_replacement_failure_rolls_back(self):
        backup = self.install()
        real_replace = __import__('os').replace
        count = 0
        def fail_second(source, destination):
            nonlocal count
            count += 1
            if count == 2: raise PermissionError('Simulated busy game file')
            return real_replace(source, destination)
        with patch('cpe_flasher.core.os.replace', side_effect=fail_second):
            with self.assertRaisesRegex(FlasherError, 'rolled back'):
                restore_backup(self.f.target, backup, lambda message: None)
        self.assertEqual((self.f.target/EXE).read_bytes(), b'rebuilt game for Rephysics')
        self.assertTrue((self.f.target/'added.py').exists())


if __name__ == '__main__': unittest.main()
