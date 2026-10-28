"""Experimental old input ZIP import retains modern target and recovery gates."""
import hashlib
import json
import unittest
import zipfile
from types import SimpleNamespace
from unittest.mock import Mock, patch

import test_cpe_flasher as fixture
from test_custom_files import Variable
from cpeloader import CPELoader, COMPONENTS
from cpe_flasher.core import EXE, FlasherError, prepare_flash, install_flash, restore_backup


class OldPortableTests(unittest.TestCase):
    setUp = fixture.FlasherTests.setUp
    tearDown = fixture.FlasherTests.tearDown
    compiler = fixture.FlasherTests.compiler
    prepare = fixture.FlasherTests.prepare

    def old_zip(self, manifest=None, helper=False):
        with zipfile.ZipFile(self.archive, 'w') as bundle:
            bundle.writestr('Old Cube/Cube 2024.exe', b'old game fixture')
            bundle.writestr('Old Cube/assets/old-menu.txt', 'old menu fixture')
            if manifest is not None: bundle.writestr('Old Cube/cpeloader_manifest.json', json.dumps(manifest))
            if helper: bundle.writestr('Old Cube/helpers/cache.exe', b'helper fixture')
        self.options.custom_portable = True
        self.options.remove_old_portable_restrictions = True
        self.options.custom_portable_sha256 = hashlib.sha256(self.archive.read_bytes()).hexdigest()
        CPELoader(self.target).unlock()

    def test_old_zip_without_loader_or_manifest_can_rebuild_install_and_restore(self):
        self.old_zip()
        original_baseline = (self.target/'cpeloader_manifest.json').read_bytes()
        plan = self.prepare()
        self.assertEqual(plan.executable_name, 'Cube 2024.exe')
        self.assertIn('EXPERIMENTAL', plan.label)
        self.assertEqual((plan.portable/'cpeloader_manifest.json').read_bytes(), original_baseline)
        self.assertTrue(all((plan.portable/name).is_file() for name in COMPONENTS))
        self.assertTrue(CPELoader(plan.portable).unlocked)
        profile = json.loads((plan.portable/'cpe-flash-profile.json').read_text())
        self.assertTrue(profile['custom_portable']['remove_old_portable_restrictions'])
        self.assertEqual(profile['custom_portable']['integrity_baseline_source'], 'installed_game')
        self.assertFalse(profile['allow_unlocked_updates'])
        self.assertTrue(CPELoader(plan.portable).changes())
        backup = install_flash(plan, lambda _: None, lambda *args: None)
        self.assertEqual((self.target/'Cube 2024.exe').read_bytes(), b'rebuilt game for Rephysics')
        with self.assertRaises(PermissionError): CPELoader(self.target).require_in_game_update()
        restore_backup(self.target, backup, lambda _: None)
        self.assertEqual((self.target/EXE).read_bytes(), b'original game')
        self.assertFalse((self.target/'Cube 2024.exe').exists())

    def test_setting_off_still_rejects_pre_loader_zip(self):
        self.old_zip(); self.options.remove_old_portable_restrictions = False
        with self.assertRaisesRegex(FlasherError, 'integrity manifest'): self.prepare()

    def test_obsolete_input_manifest_is_replaced_with_existing_target_baseline(self):
        self.old_zip(manifest={'legacy_format': 1})
        original = (self.target/'cpeloader_manifest.json').read_bytes()
        plan = self.prepare()
        self.assertEqual((plan.portable/'cpeloader_manifest.json').read_bytes(), original)

    def test_old_mode_does_not_unlock_target(self):
        self.old_zip(); (self.target/'cpeloader_state.json').unlink()
        with self.assertRaises(PermissionError): self.prepare()
        self.assertFalse((self.root/'stage').exists())

    def test_invalid_target_baseline_is_not_resealed(self):
        self.old_zip(); (self.target/'cpeloader_manifest.json').write_text('{}')
        with self.assertRaisesRegex(FlasherError, 'original integrity manifest'): self.prepare()
        self.assertFalse((self.root/'stage').exists())

    def test_custom_zip_hash_and_full_rewrite_are_still_required(self):
        self.old_zip(); self.options.custom_portable_sha256 = '0'*64
        with self.assertRaisesRegex(FlasherError, 'SHA-256 mismatch'): self.prepare()
        self.assertFalse((self.root/'stage').exists())
        self.options.custom_portable_sha256 = hashlib.sha256(self.archive.read_bytes()).hexdigest()
        for custom, rewrite in ((False, True), (True, False)):
            self.options.custom_portable = custom; self.options.full_rewrite = rewrite
            with self.subTest(custom=custom, rewrite=rewrite), self.assertRaisesRegex(FlasherError, 'Full rewrite'):
                self.prepare()

    def test_missing_source_is_not_decompiled(self):
        self.old_zip()
        with self.assertRaisesRegex(FlasherError, 'matching game source'):
            prepare_flash(self.archive, self.target, self.root/'stage', None, None,
                          self.source/'python.exe', lambda _: None, self.compiler, self.options)
        self.assertEqual((self.target/EXE).read_bytes(), b'original game')

    def test_incomplete_modern_loader_source_stops_before_compiler(self):
        self.old_zip(); (self.source/COMPONENTS[1]).unlink()
        compiler = Mock()
        with self.assertRaisesRegex(FlasherError, 'all current CPELoader components'): self.prepare(compiler)
        compiler.assert_not_called()

    def test_multiple_exes_require_exact_game_name(self):
        self.old_zip(helper=True)
        with self.assertRaisesRegex(FlasherError, 'exact filename'): self.prepare()
        self.options.custom_executable_name = 'Cube 2024.exe'
        plan = prepare_flash(self.archive, self.target, self.root/'selected', self.source, None,
                             self.source/'python.exe', lambda _: None, self.compiler, self.options)
        self.assertEqual(plan.executable_name, 'Cube 2024.exe')


class OldPortableGuiTests(unittest.TestCase):
    def app(self):
        return SimpleNamespace(remove_old_portable_restrictions=Variable(True),
                               custom_portable=Variable(True), full_rewrite=Variable(False))

    def test_declining_warning_disables_setting(self):
        from cpe_flasher.gui import FlasherApp
        app = self.app()
        with patch('cpe_flasher.gui.messagebox.askyesno', return_value=False) as confirm:
            FlasherApp.confirm_old_portable(app)
        self.assertFalse(app.remove_old_portable_restrictions.get())
        self.assertFalse(app.full_rewrite.get())
        self.assertEqual(confirm.call_args.kwargs['default'], 'no')

    def test_accepting_enables_full_rewrite(self):
        from cpe_flasher.gui import FlasherApp
        app = self.app()
        with patch('cpe_flasher.gui.messagebox.askyesno', return_value=True):
            FlasherApp.confirm_old_portable(app)
        self.assertTrue(app.full_rewrite.get())

    def test_requires_custom_zip_opt_in(self):
        from cpe_flasher.gui import FlasherApp
        app = self.app(); app.custom_portable.set(False)
        with patch('cpe_flasher.gui.messagebox.showwarning'), patch('cpe_flasher.gui.messagebox.askyesno') as confirm:
            FlasherApp.confirm_old_portable(app)
        self.assertFalse(app.remove_old_portable_restrictions.get())
        confirm.assert_not_called()

    def test_declining_per_build_warning_does_not_start_worker(self):
        from cpe_flasher.gui import FlasherApp
        app = self.app(); app.full_rewrite.set(True); app.trust = Variable(True)
        app.archive = Variable('old.zip'); app.target = Variable('installed'); app.python = Variable('python.exe')
        app.userdata = Variable('userdata'); app.custom_portable_sha256 = Variable('a'*64)
        app.allow_custom_files = Variable(False); app.start = Mock()
        with patch('cpe_flasher.gui.messagebox.askyesno', side_effect=[True, False]):
            FlasherApp.prepare(app)
        app.start.assert_not_called()


if __name__ == '__main__': unittest.main()
