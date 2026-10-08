import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from cpeloader import CPELoader, COMPONENTS, snapshot, write_json
from cpe_flasher.core import EXE, FlasherError, safe_extract, prepare_flash, install_flash, apply_project, FlashOptions


class FlasherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.target = self.root/'installed'
        self.target.mkdir()
        (self.target/EXE).write_bytes(b'original game')
        for name in COMPONENTS: (self.target/name).write_text('# loader')
        write_json(self.target/'cpeloader_manifest.json', {'files': snapshot(self.target)})
        self.source = self.root/'source'; self.source.mkdir()
        for name in (*COMPONENTS, 'the_cube_beta_summer.py', 'cube_core.py', 'summer_build.spec', 'flashed_runtime.py'):
            (self.source/name).write_text('# source')
        (self.source/'cpe').mkdir(); (self.source/'cpe'/'backend.py').write_text('# selector')
        (self.source/'cpe_rephysics').mkdir(); (self.source/'cpe_rephysics'/'physics.py').write_text('# solver')
        self.archive = self.root/'game.zip'
        with zipfile.ZipFile(self.archive, 'w') as bundle:
            for path in self.target.iterdir(): bundle.write(path, path.name)
        userdata = self.root/'userdata'; userdata.mkdir()
        write_json(userdata/'userdata.json', {'schema': 1, 'player_name': 'Tester'})
        self.options = FlashOptions(userdata)

    def tearDown(self): self.temp.cleanup()

    def compiler(self, source, python, log):
        output = source/'dist'/EXE; output.parent.mkdir()
        output.write_bytes(b'rebuilt game for Rephysics')
        return output

    def prepare(self, compiler=None):
        return prepare_flash(self.archive, self.target, self.root/'stage', self.source, None, Path('python'), lambda x: None, compiler or self.compiler, self.options)

    def test_userdata_required_before_build_or_replacement(self):
        CPELoader(self.target).unlock()
        with self.assertRaisesRegex(FlasherError, 'Userdata is required'):
            prepare_flash(self.archive, self.target, self.root/'stage', self.source, None, Path('python'))
        self.assertFalse((self.root/'stage').exists())

    def test_optional_loader_scripts_verbose_and_unlocked_zip(self):
        import json
        loader = self.root/'loader.py'; loader.write_text('# trusted loader')
        script = self.root/'startup.py'; script.write_text('# trusted startup')
        self.options.loader = loader; self.options.scripts = (script,); self.options.verbose_python = True
        CPELoader(self.target).unlock()
        plan = self.prepare()
        profile = json.loads((plan.portable/'cpe-flash-profile.json').read_text())
        self.assertTrue(profile['verbose_python'])
        self.assertFalse(profile['safety_cube_alerts'])
        self.assertTrue(profile['cpeloader_warning'])
        self.assertEqual(len(profile['scripts']), 1)
        self.assertTrue((plan.portable/profile['loader']).is_file())
        self.assertTrue(CPELoader(plan.portable).unlocked)
        with zipfile.ZipFile(plan.output_zip) as archive:
            self.assertTrue(json.loads(archive.read('cpeloader_state.json'))['unlocked'])
            self.assertIn('userdata/userdata.json', archive.namelist())

    def test_full_rewrite_backs_up_obsolete_managed_code(self):
        stale = self.target/'obsolete.py'; stale.write_text('# old managed code')
        write_json(self.target/'cpeloader_manifest.json', {'files': snapshot(self.target)})
        player = self.target/'userdata'; player.mkdir()
        (player/'save.json').write_text('{"score": 42}')
        CPELoader(self.target).unlock()
        plan = self.prepare()
        backup = install_flash(plan, lambda x: None, lambda *args: None)
        self.assertFalse(stale.exists())
        self.assertEqual((backup/'files'/'obsolete.py').read_text(), '# old managed code')
        self.assertTrue((player/'save.json').is_file())

    def test_locked_game_refuses_before_extracting_or_rebuilding(self):
        with self.assertRaises(PermissionError): self.prepare()
        self.assertFalse((self.root/'stage').exists())

    def test_build_failure_does_not_change_installed_game(self):
        CPELoader(self.target).unlock()
        def fail(*args): raise FlasherError('failed build')
        with self.assertRaises(FlasherError): self.prepare(fail)
        self.assertEqual((self.target/EXE).read_bytes(), b'original game')
        self.assertFalse((self.target/'backup').exists())

    def test_zip_flash_rebuild_backup_replace_shortcut_and_warning(self):
        CPELoader(self.target).unlock()
        plan = self.prepare()
        self.assertTrue(plan.output_zip.is_file())
        self.assertEqual((self.target/EXE).read_bytes(), b'original game')
        called = []
        def shortcut(target, output):
            self.assertEqual((target/EXE).read_bytes(), b'rebuilt game for Rephysics')
            called.append(output)
        backup = install_flash(plan, lambda x: None, shortcut)
        self.assertEqual((backup/'files'/EXE).read_bytes(), b'original game')
        self.assertTrue(called)
        self.assertTrue(CPELoader(self.target).unlocked)
        self.assertIn(EXE, CPELoader(self.target).changes())
        self.assertIn('cpe-backend.json', CPELoader(self.target).changes())

    def test_target_relocked_during_build_cannot_be_replaced(self):
        CPELoader(self.target).unlock(); plan = self.prepare()
        (self.target/'cpeloader_state.json').unlink()
        with self.assertRaises(PermissionError): install_flash(plan)
        self.assertEqual((self.target/EXE).read_bytes(), b'original game')

    def test_replacement_failure_restores_already_replaced_files(self):
        CPELoader(self.target).unlock(); plan = self.prepare()
        import os
        original = os.replace
        count = 0
        def fail_second(source, destination):
            nonlocal count
            if str(source).endswith('.cpe-flasher-writing'):
                count += 1
                if count == 2: raise PermissionError('game running')
            return original(source, destination)
        with patch('cpe_flasher.core.os.replace', side_effect=fail_second):
            with self.assertRaises(FlasherError): install_flash(plan)
        self.assertEqual((self.target/EXE).read_bytes(), b'original game')

    def test_zip_traversal_is_rejected(self):
        bad = self.root/'bad.zip'
        with zipfile.ZipFile(bad, 'w') as bundle: bundle.writestr('../outside.txt', 'escape')
        with self.assertRaises(FlasherError): safe_extract(bad, self.root/'extract')
        self.assertFalse((self.root/'outside.txt').exists())

    def test_custom_project_requires_compatible_manifest_and_package(self):
        project = self.root/'project'; project.mkdir()
        build = self.root/'build'; build.mkdir()
        portable = self.root/'portable'; portable.mkdir()
        with self.assertRaises(FlasherError): apply_project(project, build, portable)
        write_json(project/'cpe-project.json', {'api': 'CPE/1', 'name': 'Other CPE', 'version': '0.1'})
        package = project/'cpe_project'; package.mkdir()
        for name in ('__init__.py', 'physics.py'): (package/name).write_text('# compatible project')
        self.assertEqual(apply_project(project, build, portable), 'Other CPE')
        self.assertTrue((build/'cpe_project'/'physics.py').is_file())

    def test_separate_rephysics_repository_is_supported(self):
        project = self.root/'other-rephysics'; project.mkdir()
        package = project/'cpe_rephysics'; package.mkdir()
        (package/'__init__.py').write_text('# selected repository')
        (package/'physics.py').write_text('# new solver')
        build = self.root/'other-build'; build.mkdir()
        portable = self.root/'other-portable'; portable.mkdir()
        self.assertEqual(apply_project(project, build, portable), 'CPE Rephysics')
        self.assertEqual((build/'cpe_rephysics'/'physics.py').read_text(), '# new solver')
        self.assertEqual((portable/'cpe_rephysics'/'physics.py').read_text(), '# new solver')

    def test_existing_player_settings_are_preserved(self):
        with zipfile.ZipFile(self.archive, 'a') as bundle: bundle.writestr('settings.json', '{"volume": 1}')
        (self.target/'settings.json').write_text('{"volume": 0.1}')
        CPELoader(self.target).unlock()
        plan = self.prepare()
        install_flash(plan, lambda x: None, lambda *args: None)
        self.assertEqual((self.target/'settings.json').read_text(), '{"volume": 0.1}')


if __name__ == '__main__': unittest.main()
