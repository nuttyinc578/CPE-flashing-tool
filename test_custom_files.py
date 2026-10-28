"""Opted-in custom menu/file staging, source round trips and consent checks."""
import hashlib
import json
import unittest
import zipfile
from types import SimpleNamespace
from unittest.mock import Mock, patch

import test_cpe_flasher as fixture
from cpeloader import CPELoader
from cpe_flasher.core import FlasherError, prepare_flash, install_flash, restore_backup


class CustomFilesTests(unittest.TestCase):
    setUp = fixture.FlasherTests.setUp
    tearDown = fixture.FlasherTests.tearDown
    compiler = fixture.FlasherTests.compiler
    prepare = fixture.FlasherTests.prepare

    def configure(self):
        self.options.custom_portable = True
        self.options.allow_custom_files = True
        self.options.custom_portable_sha256 = hashlib.sha256(self.archive.read_bytes()).hexdigest()
        CPELoader(self.target).unlock()
        for name, text in {'menus/__init__.py': '', 'menus/main.py': "MENU_TITLE = 'My custom cube menu'\n",
                           'assets/menu.json': '{"theme": "purple"}', 'custom-files/palette.dat': 'custom palette',
                           '.env': 'private fixture', 'credentials.json': '{"fixture": true}',
                           'userdata/local.txt': 'private fixture', 'backup/old.txt': 'backup fixture',
                           'cpeloader_state.json': '{}', 'cpeloader_manifest.json': '{}',
                           'private.key': 'private fixture'}.items():
            path = self.source/name; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(text)
        (self.source/'cube_core.py').write_text('from menus.main import MENU_TITLE\n')

    def test_custom_menus_and_assets_survive_compile_zip_install_and_restore(self):
        self.configure()
        def compiler(build, python, log):
            self.assertIn('My custom cube menu', (build/'menus/main.py').read_text())
            self.assertTrue((build/'assets/menu.json').is_file())
            self.assertTrue((build/'custom-files/palette.dat').is_file())
            self.assertIn('from menus.main import MENU_TITLE', (build/'cube_core.py').read_text())
            self.assertIn('def require_in_game_update', (build/'cpeloader.py').read_text())
            return self.compiler(build, python, log)
        plan = self.prepare(compiler)
        with zipfile.ZipFile(plan.portable/'game-source.zip') as bundle:
            self.assertIn('menus/main.py', bundle.namelist())
            self.assertIn('assets/menu.json', bundle.namelist())
            self.assertNotIn('cpeloader_state.json', bundle.namelist())
        profile = json.loads((plan.portable/'cpe-flash-profile.json').read_text())
        self.assertTrue(profile['custom_portable']['allow_custom_files'])
        self.assertFalse(profile['allow_unlocked_updates'])
        self.assertTrue(profile['cpeloader_warning'])
        backup = install_flash(plan, lambda _: None, lambda *args: None)
        self.assertTrue((self.target/'menus/main.py').is_file())
        self.assertTrue((self.target/'assets/menu.json').is_file())
        with self.assertRaises(PermissionError): CPELoader(self.target).require_in_game_update()
        restore_backup(self.target, backup, lambda _: None)
        self.assertFalse((self.target/'menus/main.py').exists())
        self.assertFalse((self.target/'assets/menu.json').exists())

    def test_common_private_source_files_and_state_are_not_copied(self):
        self.configure(); plan = self.prepare()
        for name in ('.env', 'credentials.json', 'userdata/local.txt', 'backup/old.txt', 'private.key'):
            with self.subTest(name=name):
                self.assertFalse((self.root/'stage/game-build'/name).exists())
                self.assertFalse((plan.portable/name).exists())

    def test_new_file_option_is_off_by_default(self):
        self.configure(); self.options.allow_custom_files = False
        plan = self.prepare()
        self.assertFalse((plan.portable/'menus/main.py').exists())
        self.assertFalse((self.root/'stage/game-build/assets/menu.json').exists())

    def test_requires_custom_zip_and_full_rewrite_before_staging(self):
        self.configure()
        for custom, rewrite in ((False, True), (True, False)):
            self.options.custom_portable = custom; self.options.full_rewrite = rewrite
            with self.subTest(custom=custom, rewrite=rewrite), self.assertRaisesRegex(FlasherError, 'Full rewrite'):
                self.prepare()
            self.assertFalse((self.root/'stage').exists())

    def test_embedded_complete_source_and_second_flash_preserve_menu_files(self):
        self.configure()
        source_zip = self.root/'source.zip'
        with zipfile.ZipFile(source_zip, 'w') as bundle:
            for path in self.source.rglob('*'):
                if path.is_file(): bundle.write(path, path.relative_to(self.source).as_posix())
        with zipfile.ZipFile(self.archive, 'a') as bundle: bundle.write(source_zip, 'game-source.zip')
        self.options.custom_portable_sha256 = hashlib.sha256(self.archive.read_bytes()).hexdigest()
        first = prepare_flash(self.archive, self.target, self.root/'first', None, None,
                              self.source/'python.exe', lambda _: None, self.compiler, self.options)
        self.options.custom_portable_sha256 = hashlib.sha256(first.output_zip.read_bytes()).hexdigest()
        second = prepare_flash(first.output_zip, self.target, self.root/'second', None, None,
                               self.source/'python.exe', lambda _: None, self.compiler, self.options)
        self.assertTrue((second.portable/'menus/main.py').is_file())
        with zipfile.ZipFile(second.portable/'game-source.zip') as bundle: self.assertIn('assets/menu.json', bundle.namelist())

    def test_missing_embedded_source_still_requires_complete_source(self):
        self.configure()
        with self.assertRaisesRegex(FlasherError, 'matching game source'):
            prepare_flash(self.archive, self.target, self.root/'missing-source', None, None,
                          self.source/'python.exe', lambda _: None, self.compiler, self.options)


class Variable:
    def __init__(self, value): self.value = value
    def get(self): return self.value
    def set(self, value): self.value = value


class CustomFilesGuiTests(unittest.TestCase):
    def app(self):
        return SimpleNamespace(allow_custom_files=Variable(True), custom_portable=Variable(True),
            source=Variable('bundled-source'), bundled_source='bundled-source', full_rewrite=Variable(False))

    def test_decline_disables_custom_files_without_changing_source(self):
        from cpe_flasher.gui import FlasherApp
        app = self.app()
        with patch('cpe_flasher.gui.messagebox.askyesno', return_value=False) as confirm:
            FlasherApp.confirm_custom_files(app)
        self.assertFalse(app.allow_custom_files.get())
        self.assertEqual(app.source.get(), 'bundled-source')
        self.assertFalse(app.full_rewrite.get())
        self.assertEqual(confirm.call_args.kwargs['default'], 'no')
        self.assertIn('menus', confirm.call_args.args[1])
        self.assertIn('SECURITY RISK', confirm.call_args.args[1])

    def test_accept_clears_only_default_source_and_enables_full_rewrite(self):
        from cpe_flasher.gui import FlasherApp
        for source in ('bundled-source', 'my-custom-source'):
            app = self.app(); app.source.set(source)
            with patch('cpe_flasher.gui.messagebox.askyesno', return_value=True):
                FlasherApp.confirm_custom_files(app)
            self.assertEqual(app.source.get(), '' if source == 'bundled-source' else source)
            self.assertTrue(app.full_rewrite.get())

    def test_requires_custom_zip_opt_in(self):
        from cpe_flasher.gui import FlasherApp
        app = self.app(); app.custom_portable.set(False)
        with patch('cpe_flasher.gui.messagebox.showwarning'), patch('cpe_flasher.gui.messagebox.askyesno') as confirm:
            FlasherApp.confirm_custom_files(app)
        self.assertFalse(app.allow_custom_files.get())
        confirm.assert_not_called()

    def test_declining_build_confirmation_never_starts_worker(self):
        from cpe_flasher.gui import FlasherApp
        app = self.app(); app.full_rewrite.set(True)
        app.trust = Variable(True); app.archive = Variable('custom.zip'); app.target = Variable('installed')
        app.python = Variable('python.exe'); app.userdata = Variable('userdata')
        app.custom_portable_sha256 = Variable('a'*64); app.start = Mock()
        with patch('cpe_flasher.gui.messagebox.askyesno', side_effect=[True, False]):
            FlasherApp.prepare(app)
        app.start.assert_not_called()


if __name__ == '__main__': unittest.main()
