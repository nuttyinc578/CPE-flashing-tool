import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cpeloader import CPELoader, COMPONENTS, snapshot, write_json
from cpe_flasher.core import FlashOptions, apply_options, locate_games, EXE
from cpe_flasher.python_discovery import resolve_python, discover_python, check_python


class UpdateOverrideTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        for name in COMPONENTS: (self.root/name).write_text('# loader')
        write_json(self.root/'cpeloader_manifest.json', {'files': snapshot(self.root)})
        self.loader = CPELoader(self.root)
        self.loader.unlock()

    def tearDown(self): self.temp.cleanup()

    def profile(self, enabled=True):
        write_json(self.root/'cpe-flash-profile.json', {'schema': 1, 'allow_unlocked_updates': enabled, 'nuttymod_mods': ['cpeloader-unlocked-updates']})

    def test_opt_in_allows_updates_keeps_warnings_and_unlock(self):
        with self.assertRaises(PermissionError): self.loader.require_in_game_update()
        self.profile()
        self.loader.require_in_game_update()
        self.assertTrue(self.loader.unlocked)
        self.assertIn('cpe-flash-profile.json', self.loader.changes())

    def test_disabled_or_malformed_profile_does_not_enable_override(self):
        self.profile(False)
        with self.assertRaises(PermissionError): self.loader.require_in_game_update()
        (self.root/'cpe-flash-profile.json').write_text('invalid')
        with self.assertRaises(PermissionError): self.loader.require_in_game_update()

    def test_override_cannot_flash_locked_or_incomplete_loader(self):
        self.profile()
        (self.root/COMPONENTS[0]).unlink()
        self.assertFalse(self.loader.unlocked_updates_enabled)
        with self.assertRaises(PermissionError): self.loader.require_flash()
        with self.assertRaises(PermissionError): self.loader.require_in_game_update()

    def test_corrupt_state_still_blocks_updates(self):
        self.profile()
        self.loader.path.write_text('invalid')
        with self.assertRaises(PermissionError): self.loader.require_in_game_update()

    def test_flash_profile_records_opt_in_in_build_and_portable(self):
        userdata = self.root/'userdata'; userdata.mkdir()
        build = self.root/'build'; build.mkdir()
        portable = self.root/'portable'; portable.mkdir()
        (build/'flashed_runtime.py').write_text('# runtime')
        apply_options(FlashOptions(userdata, allow_unlocked_updates=True), build, portable)
        for folder in (build, portable):
            profile = json.loads((folder/'cpe-flash-profile.json').read_text())
            self.assertTrue(profile['allow_unlocked_updates'])
            self.assertTrue(profile['cpeloader_warning'])


class PythonDiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self): self.temp.cleanup()

    def test_install_directory_and_venv_directory_resolve(self):
        direct = self.root/'Python312'; direct.mkdir()
        (direct/'python.exe').write_text('test fixture')
        venv = self.root/'venv'; (venv/'Scripts').mkdir(parents=True)
        (venv/'Scripts'/'python.exe').write_text('test fixture')
        self.assertEqual(resolve_python(direct), direct/'python.exe')
        self.assertEqual(resolve_python(venv), venv/'Scripts'/'python.exe')

    def test_codex_runtime_and_flashing_executable_are_not_compilers(self):
        codex = self.root/'codex-runtimes'; codex.mkdir()
        (codex/'python.exe').write_text('test fixture')
        with self.assertRaises(ValueError): resolve_python(codex)
        (self.root/'CPE Flasher Tool.exe').write_text('test fixture')
        with self.assertRaises(ValueError): resolve_python(self.root/'CPE Flasher Tool.exe')

    def test_missing_packages_give_interpreter_specific_instruction(self):
        python = self.root/'python.exe'; python.write_text('test fixture')
        result = type('Result', (), {'returncode': 0, 'stdout': '{"version":[3,12,1],"missing":["pygame"]}'})()
        with patch('cpe_flasher.python_discovery.subprocess.run', return_value=result):
            with self.assertRaisesRegex(ValueError, 'Missing compiler packages: pygame'):
                check_python(python)

    def test_game_detection_does_not_use_cwd(self):
        (self.root/EXE).write_text('test fixture')
        for name in COMPONENTS: (self.root/name).write_text('# loader')
        with patch('cpe_flasher.core.Path.cwd', return_value=self.root), patch.dict('os.environ', {'LOCALAPPDATA': str(self.root/'none')}):
            self.assertNotIn(self.root, locate_games())
