"""Missing-source errors must not be confused with old ZIP restriction state."""
import hashlib
import shutil
import unittest
import zipfile
from types import SimpleNamespace
from unittest.mock import Mock, patch

import test_cpe_flasher as fixture
from test_custom_files import Variable
from cpeloader import CPELoader
from cpe_flasher.core import FlasherError, prepare_flash, bundled_source_path


class SourceSelectionTests(unittest.TestCase):
    setUp = fixture.FlasherTests.setUp
    tearDown = fixture.FlasherTests.tearDown
    compiler = fixture.FlasherTests.compiler

    def run_prepare(self, *, source=None, bundle=True, compiler=None):
        CPELoader(self.target).unlock()
        return prepare_flash(self.archive, self.target, self.root/'stage', source, None,
            self.source/'python.exe', lambda _: None, compiler or self.compiler, self.options,
            bundled_source=self.source if bundle else None)

    def custom_zip(self):
        self.options.custom_portable = True
        self.options.custom_portable_sha256 = hashlib.sha256(self.archive.read_bytes()).hexdigest()

    def test_modern_zip_without_source_works_with_old_restrictions_removal_off(self):
        self.assertFalse(self.options.remove_old_portable_restrictions)
        plan = self.run_prepare()
        self.assertTrue(plan.output_zip.is_file())
        self.assertTrue((plan.portable/'game-source.zip').is_file())

    def test_old_zip_without_source_uses_bundle_when_restrictions_removed(self):
        with zipfile.ZipFile(self.archive, 'w') as bundle: bundle.writestr('Old Cube.exe', b'old game fixture')
        self.custom_zip(); self.options.remove_old_portable_restrictions = True
        plan = self.run_prepare()
        self.assertEqual(plan.executable_name, 'Old Cube.exe')
        self.assertTrue((plan.portable/'cpeloader_manifest.json').is_file())

    def test_missing_source_error_does_not_claim_zip_is_old(self):
        with self.assertRaises(FlasherError) as error: self.run_prepare(bundle=False)
        self.assertIn('Rebuild source missing', str(error.exception))
        self.assertNotIn('Older portable ZIP:', str(error.exception))
        self.assertFalse((self.target/'backup').exists())

    def test_custom_menu_source_is_not_replaced_by_bundle_automatically(self):
        self.custom_zip(); self.options.allow_custom_files = True
        compiler = Mock()
        with self.assertRaisesRegex(FlasherError, 'bundled source is not substituted'):
            self.run_prepare(compiler=compiler)
        compiler.assert_not_called()

    def embedded_source(self, complete=True):
        archive = self.root/'embedded.zip'
        with zipfile.ZipFile(archive, 'w') as bundle:
            if complete:
                for path in self.source.rglob('*'):
                    if path.is_file() and path.name != 'cube_core.py':
                        bundle.write(path, path.relative_to(self.source).as_posix())
                bundle.writestr('cube_core.py', '# embedded source selected')
            else: bundle.writestr('README.txt', 'incomplete source fixture')
        with zipfile.ZipFile(self.archive, 'a') as bundle: bundle.write(archive, 'game-source.zip')
        self.custom_zip()

    def test_embedded_source_precedes_bundled_fallback(self):
        self.embedded_source()
        def compiler(build, python, log):
            self.assertEqual((build/'cube_core.py').read_text(), '# embedded source selected')
            return self.compiler(build, python, log)
        self.run_prepare(compiler=compiler)

    def test_invalid_embedded_source_is_not_hidden_by_bundle_fallback(self):
        self.embedded_source(complete=False)
        with self.assertRaisesRegex(FlasherError, 'matching game source'): self.run_prepare()

    def test_invalid_explicit_source_is_not_hidden_by_bundle_fallback(self):
        incomplete = self.root/'incomplete'; incomplete.mkdir()
        with self.assertRaisesRegex(FlasherError, 'matching game source'):
            self.run_prepare(source=incomplete)

    def test_development_staged_bundle_is_found(self):
        runtime = self.root/'development'
        staged = runtime/'build'/'flasher-source'; staged.parent.mkdir(parents=True)
        shutil.copytree(self.source, staged)
        self.assertEqual(bundled_source_path(runtime), staged.resolve())

    def test_incomplete_bundle_is_not_offered(self):
        runtime = self.root/'incomplete-runtime'; runtime.mkdir()
        (runtime/'cube_core.py').write_text('# incomplete fixture')
        self.assertIsNone(bundled_source_path(runtime))


class SourceSelectionGuiTests(unittest.TestCase):
    def app(self):
        return SimpleNamespace(allow_custom_files=Variable(True), custom_portable=Variable(True),
            source=Variable('bundle'), bundled_source='bundle', full_rewrite=Variable(False),
            _source_cleared_for_custom_files=False)

    def test_switching_custom_files_off_restores_only_auto_cleared_bundle(self):
        from cpe_flasher.gui import FlasherApp
        app = self.app()
        with patch('cpe_flasher.gui.messagebox.askyesno', return_value=True):
            FlasherApp.confirm_custom_files(app)
        self.assertEqual(app.source.get(), '')
        app.allow_custom_files.set(False)
        FlasherApp.confirm_custom_files(app)
        self.assertEqual(app.source.get(), 'bundle')

    def test_switching_off_keeps_deliberately_chosen_source_or_blank(self):
        from cpe_flasher.gui import FlasherApp
        for source in ('custom-source', ''):
            app = self.app(); app._source_cleared_for_custom_files = True
            app.source.set(source); FlasherApp.source_edited(app)
            app.allow_custom_files.set(False); FlasherApp.confirm_custom_files(app)
            self.assertEqual(app.source.get(), source)

    def test_bundled_button_warns_before_replacing_custom_source(self):
        from cpe_flasher.gui import FlasherApp
        app = self.app(); app.source.set('custom-source')
        with patch('cpe_flasher.gui.messagebox.askyesno', return_value=False) as confirm:
            FlasherApp.use_bundled_source(app)
        self.assertEqual(app.source.get(), 'custom-source')
        self.assertEqual(confirm.call_args.kwargs['default'], 'no')

    def test_bundled_button_restores_base_source_when_custom_mode_off(self):
        from cpe_flasher.gui import FlasherApp
        app = self.app(); app.source.set(''); app.allow_custom_files.set(False)
        FlasherApp.use_bundled_source(app)
        self.assertEqual(app.source.get(), 'bundle')


if __name__ == '__main__': unittest.main()
