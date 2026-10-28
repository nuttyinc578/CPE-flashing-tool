"""Custom ZIP opt-in, checksum, update policy and GUI wiring regressions."""
import hashlib
import io
import json
import tarfile
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from cpeloader import CPELoader, write_json
from cpe_flasher.core import (EXE, FlasherError, verify_custom_portable, install_flash,
    restore_backup, select_executable, create_shortcut, compile_game)
from cpe_flasher.nuttyroot import NuttyRootInputs
import test_cpe_flasher


class CustomPortableTests(unittest.TestCase):
    setUp = test_cpe_flasher.FlasherTests.setUp
    tearDown = test_cpe_flasher.FlasherTests.tearDown
    compiler = test_cpe_flasher.FlasherTests.compiler
    prepare = test_cpe_flasher.FlasherTests.prepare
    def custom_archive(self):
        with zipfile.ZipFile(self.archive, 'a') as bundle:
            bundle.writestr('nuttymod-runtime.txt', 'custom runtime fixture')
        self.options.custom_portable = True
        self.options.custom_portable_sha256 = hashlib.sha256(self.archive.read_bytes()).hexdigest()
        CPELoader(self.target).unlock()

    def test_default_rejects_modified_portable(self):
        self.custom_archive()
        self.options.custom_portable = False
        with self.assertRaisesRegex(FlasherError, 'release integrity manifest'):
            self.prepare()

    def test_custom_zip_compiles_and_installs_with_owner_update_policy(self):
        self.custom_archive()
        self.options.allow_unlocked_updates = True
        plan = self.prepare()
        self.assertIn('UNOFFICIAL', plan.label)
        profile = json.loads((plan.portable/'cpe-flash-profile.json').read_text())
        self.assertEqual(profile['custom_portable']['sha256'], self.options.custom_portable_sha256)
        self.assertEqual(profile['custom_portable']['update_provider'], 'custom_zip_owner')
        self.assertFalse(profile['allow_unlocked_updates'])
        self.assertEqual(profile['nuttymod_mods'], [])
        self.assertTrue(profile['cpeloader_warning'])
        with zipfile.ZipFile(plan.output_zip) as bundle:
            self.assertEqual(json.loads(bundle.read('cpe-flash-profile.json')), profile)
        backup = install_flash(plan, lambda message: None, lambda *args: None)
        self.assertTrue((backup/'manifest.json').is_file())
        self.assertEqual((self.target/'nuttymod-runtime.txt').read_text(), 'custom runtime fixture')
        self.assertTrue(CPELoader(self.target).changes())
        with self.assertRaisesRegex(PermissionError, 'owner of the custom ZIP'):
            CPELoader(self.target).require_in_game_update()

    def test_missing_invalid_or_wrong_sha_stops_before_extracting(self):
        self.custom_archive()
        for expected in ('', 'x'*64, 'a'*63, '0'*64):
            self.options.custom_portable_sha256 = expected
            with self.subTest(expected=expected), self.assertRaisesRegex(FlasherError, 'SHA-256'):
                self.prepare()
            self.assertFalse((self.root/'stage').exists())
        self.assertEqual((self.target/'The Cube Beta Halloween Update.exe').read_bytes(), b'original game')

    def test_owner_hash_accepts_uppercase_and_whitespace(self):
        self.custom_archive()
        self.assertEqual(verify_custom_portable(self.archive, ' '+self.options.custom_portable_sha256.upper()+'\n'),
                         self.options.custom_portable_sha256)

    def test_missing_or_invalid_manifest_still_rejected(self):
        self.custom_archive()
        for manifest in (None, {'files': []}, {'files': {'game.py': 'not-a-hash'}}):
            with zipfile.ZipFile(self.archive, 'w') as bundle:
                for path in self.target.iterdir():
                    if path.name != 'cpeloader_manifest.json': bundle.write(path, path.name)
                if manifest is not None: bundle.writestr('cpeloader_manifest.json', json.dumps(manifest))
            self.options.custom_portable_sha256 = hashlib.sha256(self.archive.read_bytes()).hexdigest()
            with self.subTest(manifest=manifest), self.assertRaisesRegex(FlasherError, 'integrity manifest'):
                self.prepare()
            # Each rejected archive has its own isolated staging directory.
            self.root = self.root/'next'; self.root.mkdir()

    def test_custom_setting_does_not_bypass_initial_unlock(self):
        self.options.custom_portable = True
        self.options.custom_portable_sha256 = hashlib.sha256(self.archive.read_bytes()).hexdigest()
        with self.assertRaises(PermissionError): self.prepare()
        self.assertFalse((self.root/'stage').exists())

    def test_custom_build_blocks_updates_after_relock_and_despite_bypass(self):
        self.custom_archive()
        for marker in ({'unofficial': True}, None, 'invalid metadata'):
            write_json(self.target/'cpe-flash-profile.json', {'schema': 1, 'custom_portable': marker,
                'allow_unlocked_updates': True, 'nuttymod_mods': ['cpeloader-unlocked-updates']})
            for unlocked in (True, False):
                write_json(self.target/'cpeloader_state.json', {'unlocked': unlocked})
                with self.subTest(marker=marker, unlocked=unlocked):
                    self.assertFalse(CPELoader(self.target).unlocked_updates_enabled)
                    with self.assertRaisesRegex(PermissionError, 'Unofficial custom portable'):
                        CPELoader(self.target).require_in_game_update()

    def root_packages(self):
        def make_tar(name, files):
            path = self.root/name
            with tarfile.open(path, 'w') as bundle:
                for filename, data in files.items():
                    data = data.encode()
                    member = tarfile.TarInfo(filename); member.size = len(data)
                    bundle.addfile(member, io.BytesIO(data))
            return path
        loader = self.root/'nuttymod_loader.py'; loader.write_text('# test loader')
        loader_zip = self.root/'loader.zip'
        with zipfile.ZipFile(loader_zip, 'w') as bundle:
            bundle.write(loader, 'nuttymod_loader/nuttymod_loader.py')
        root_tar = make_tar('root.tar', {'root_manifest.json': json.dumps({'schema': 1, 'version': 'test'})})
        rootmode = make_tar('rootmode.tar', {'rootmode_manifest.json': json.dumps({'schema': 1, 'library': '1.2'}),
            'root_mode_runtime.py': '# test runtime', 'root_mode_loader.py': '# test library loader'})
        hashes = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in
            (('loader_py', loader), ('loader_zip', loader_zip), ('root_tar', root_tar), ('rootmode_tar', rootmode))}
        verification = make_tar('verification.tar', {'verification.json': json.dumps({'schema': 1, 'version': 'test', 'sha256': hashes})})
        self.options.loader = loader
        self.options.nuttymod_root = NuttyRootInputs(loader_zip, root_tar, verification, None, rootmode)
        (self.source/'nuttymod_root_support.py').write_text('# test support')
        (self.source/'flashed_runtime.py').write_text('def initialize_nuttymod(): pass')

    def test_custom_nuttymod_root_accepts_custom_sha_without_official_checksums(self):
        self.custom_archive(); self.root_packages()
        plan = self.prepare()
        profile = json.loads((plan.portable/'cpe-flash-profile.json').read_text())
        self.assertEqual(profile['nuttymod_root']['version'], 'test')
        self.assertTrue(profile['custom_portable']['unofficial'])
        self.assertFalse(profile['allow_unlocked_updates'])

    def test_custom_nuttymod_keeps_package_verification_required(self):
        self.custom_archive(); self.root_packages()
        self.options.loader.write_text('# changed loader fixture')
        with self.assertRaisesRegex(FlasherError, 'verification TAR does not match'):
            self.prepare()
        self.assertEqual((self.target/'The Cube Beta Halloween Update.exe').read_bytes(), b'original game')

    def test_official_nuttymod_still_requires_official_checksums(self):
        self.custom_archive(); self.root_packages()
        self.options.custom_portable = False
        with self.assertRaisesRegex(FlasherError, 'official SHA256SUMS'):
            self.prepare()
        self.assertFalse((self.root/'stage').exists())

    def renamed_archive(self, name='NuttyMod Runtime.EXE'):
        self.archive = self.root/'My own portable build.zip'
        with zipfile.ZipFile(self.archive, 'w') as bundle:
            for path in self.target.iterdir():
                bundle.write(path, 'Custom portable folder/'+(name if path.name == EXE else path.name))
            bundle.writestr('Custom portable folder/helpers/helper.exe', b'helper fixture')
        self.options.custom_portable = True
        self.options.custom_portable_sha256 = hashlib.sha256(self.archive.read_bytes()).hexdigest()
        CPELoader(self.target).unlock()

    def test_custom_exe_and_zip_names_install_shortcut_and_restore(self):
        name = 'NuttyMod Runtime.EXE'
        self.renamed_archive(name)
        (self.target/'The Cube Beta.lnk').write_bytes(b'old shortcut')
        plan = self.prepare()
        self.assertEqual(plan.executable_name, name)
        self.assertEqual(plan.output_zip.name, 'My own portable build-Flashed.zip')
        self.assertFalse((plan.portable/EXE).exists())
        with zipfile.ZipFile(plan.output_zip) as bundle: self.assertIn(name, bundle.namelist())
        with patch('cpe_flasher.core.create_shortcut') as shortcut:
            backup = install_flash(plan, lambda message: None)
        shortcut.assert_called_once_with(self.target.resolve(), self.target/'The Cube Beta.lnk', name)
        self.assertEqual((self.target/name).read_bytes(), b'rebuilt game for Rephysics')
        self.assertFalse((self.target/EXE).exists())
        self.assertEqual((backup/'files'/EXE).read_bytes(), b'original game')
        restore_backup(self.target, backup, lambda message: None)
        self.assertEqual((self.target/EXE).read_bytes(), b'original game')
        self.assertFalse((self.target/name).exists())
        self.assertEqual((self.target/'The Cube Beta.lnk').read_bytes(), b'old shortcut')

    def test_renamed_installed_exe_replaced_even_without_full_rewrite(self):
        self.renamed_archive('New Custom.exe')
        (self.target/EXE).rename(self.target/'Old Custom.exe')
        self.options.full_rewrite = False
        plan = self.prepare()
        self.assertEqual(plan.previous_executable_name, 'Old Custom.exe')
        backup = install_flash(plan, lambda message: None, lambda *args: None)
        self.assertFalse((self.target/'Old Custom.exe').exists())
        restore_backup(self.target, backup, lambda message: None)
        self.assertEqual((self.target/'Old Custom.exe').read_bytes(), b'original game')

    def test_explicit_names_resolve_multiple_custom_exes(self):
        self.renamed_archive('My Game.exe')
        with zipfile.ZipFile(self.archive, 'a') as bundle:
            bundle.writestr('Custom portable folder/Other Game.exe', b'other fixture')
        (self.target/EXE).rename(self.target/'Installed Game.exe')
        (self.target/'Other.exe').write_bytes(b'other installed fixture')
        self.options.custom_executable_name = 'My Game.exe'
        self.options.target_executable_name = 'Installed Game.exe'
        self.options.custom_portable_sha256 = hashlib.sha256(self.archive.read_bytes()).hexdigest()
        plan = self.prepare()
        self.assertEqual(plan.executable_name, 'My Game.exe')
        self.assertEqual(plan.previous_executable_name, 'Installed Game.exe')
        self.assertEqual((self.target/'Other.exe').read_bytes(), b'other installed fixture')

    def test_ambiguous_custom_exe_requires_explicit_name(self):
        self.renamed_archive('My Game.exe')
        with zipfile.ZipFile(self.archive, 'a') as bundle:
            bundle.writestr('Custom portable folder/Other Game.exe', b'other fixture')
        self.options.custom_portable_sha256 = hashlib.sha256(self.archive.read_bytes()).hexdigest()
        with self.assertRaisesRegex(FlasherError, 'exact filename'): self.prepare()
        self.assertEqual((self.target/EXE).read_bytes(), b'original game')

    def test_renamed_zip_with_standard_exe_already_supported(self):
        renamed = self.root/'Any portable name.ZIP'
        self.archive.rename(renamed); self.archive = renamed
        CPELoader(self.target).unlock()
        self.assertEqual(self.prepare().executable_name, EXE)

    def test_missing_or_invalid_custom_exe_name_stops_before_staging(self):
        self.custom_archive()
        for name in ('Missing.exe', '../Game.exe', 'folder\\Game.exe', 'NUL.exe', 'Game.exe '):
            self.options.target_executable_name = name
            with self.subTest(name=name), self.assertRaises(FlasherError): self.prepare()
            self.assertFalse((self.root/'stage').exists())

    def test_standard_mode_still_requires_standard_exe_name(self):
        (self.target/EXE).rename(self.target/'Renamed.exe')
        with self.assertRaisesRegex(FlasherError, 'selected game executable'):
            self.prepare()

    def test_shortcut_target_uses_custom_exe_name(self):
        destination = self.target/'custom.lnk'
        def shell(*args, **kwargs):
            self.assertEqual(kwargs['env']['CPE_TARGET'], str(self.target/'A Custom Game.EXE'))
            destination.write_bytes(b'shortcut fixture')
            return SimpleNamespace(returncode=0, stderr='')
        with patch('cpe_flasher.core.subprocess.run', side_effect=shell):
            create_shortcut(self.target, destination, 'A Custom Game.EXE')

    def test_compiler_accepts_renamed_spec_output(self):
        def build_command(*args):
            output = self.source/'dist'/'My compiled game.exe'
            output.parent.mkdir(exist_ok=True); output.write_bytes(b'game fixture'*128)
        with patch('cpe_flasher.core.check_python', return_value=Path('python.exe')), patch('cpe_flasher.core.run_checked', side_effect=build_command):
            self.assertEqual(compile_game(self.source, Path('python.exe'), lambda message: None).name, 'My compiled game.exe')


class CustomPortableGuiTests(unittest.TestCase):
    def test_declining_custom_warning_switches_option_off(self):
        from cpe_flasher.gui import FlasherApp
        flag = Mock(); flag.get.return_value = True
        with patch('cpe_flasher.gui.messagebox.askyesno', return_value=False) as confirm:
            FlasherApp.confirm_custom_portable(SimpleNamespace(custom_portable=flag))
        flag.set.assert_called_once_with(False)
        self.assertEqual(confirm.call_args.kwargs['default'], 'no')
        self.assertIn('SECURITY RISK', confirm.call_args.args[1])

    def test_declining_build_warning_never_starts_compiler(self):
        from cpe_flasher.gui import FlasherApp
        def variable(value):
            return SimpleNamespace(get=lambda: value)
        app = SimpleNamespace(trust=variable(True), archive=variable('custom.zip'), target=variable('installed'),
            python=variable('python.exe'), userdata=variable('userdata'), custom_portable=variable(True),
            custom_portable_sha256=variable('a'*64), start=Mock())
        with patch('cpe_flasher.gui.messagebox.askyesno', return_value=False) as confirm:
            FlasherApp.prepare(app)
        app.start.assert_not_called()
        self.assertEqual(confirm.call_count, 1)
        self.assertIn('SECURITY RISK', confirm.call_args.args[1])


if __name__ == '__main__': unittest.main()
