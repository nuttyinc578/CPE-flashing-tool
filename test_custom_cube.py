import hashlib
import io
import json
import tarfile
import unittest
import test_cpe_flasher as fixtures
from cpeloader import CPELoader
from cpe_flasher.core import FlasherError, install_flash, restore_backup


class CustomCubeTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.FlasherTests()
        self.fixture.setUp()
        self.fixture.options.custom_cube_tar = self.fixture.root/'custom.tar'

    def tearDown(self): self.fixture.tearDown()

    def package(self, bad_hash=False):
        code = b'def on_load(app, userdata):\n    app.custom_cube_enabled = True\n'
        manifest = {'schema':1, 'api':'CubeBeta/1', 'name':'Test Custom Cube', 'version':'1',
                    'startup':'python/custom_cube.py', 'files':{'python/custom_cube.py': '0'*64 if bad_hash else hashlib.sha256(code).hexdigest()}}
        with tarfile.open(self.fixture.options.custom_cube_tar, 'w') as archive:
            for name, data in [('custom-cube.json', json.dumps(manifest).encode()), ('python/custom_cube.py', code)]:
                info = tarfile.TarInfo(name); info.size = len(data)
                archive.addfile(info, io.BytesIO(data))

    def test_custom_overlay_profile_source_zip_install_and_restore(self):
        self.package()
        CPELoader(self.fixture.target).unlock()
        plan = self.fixture.prepare()
        self.assertTrue((plan.portable/'custom_cube.py').exists())
        profile = json.loads((plan.portable/'cpe-flash-profile.json').read_text())
        self.assertEqual(profile['custom_cube']['name'], 'Test Custom Cube')
        self.assertIn('flash_scripts/custom-cube-startup.py', profile['scripts'])
        self.assertTrue(profile['cpeloader_warning'])
        backup = install_flash(plan, lambda _:None, lambda *args:None)
        self.assertIn('custom_cube.py', CPELoader(self.fixture.target).changes())
        restore_backup(self.fixture.target, backup, lambda _:None)
        self.assertFalse((self.fixture.target/'custom_cube.py').exists())
        self.assertEqual((self.fixture.target/fixtures.EXE).read_bytes(), b'original game')

    def test_checksum_mismatch_stops_before_compiler(self):
        self.package(bad_hash=True)
        CPELoader(self.fixture.target).unlock()
        def compiler(*args): self.fail('Compiler must not run')
        with self.assertRaisesRegex(FlasherError, 'checksum'): self.fixture.prepare(compiler)
        self.assertEqual((self.fixture.target/fixtures.EXE).read_bytes(), b'original game')

    def test_custom_cube_requires_full_rewrite(self):
        self.package()
        CPELoader(self.fixture.target).unlock()
        self.fixture.options.full_rewrite = False
        with self.assertRaisesRegex(FlasherError, 'Full rewrite'): self.fixture.prepare()
        self.assertFalse((self.fixture.root/'stage').exists())

    def test_ortain_project_sets_loading_preset(self):
        from pathlib import Path
        self.fixture.options.custom_cube_tar = None
        CPELoader(self.fixture.target).unlock()
        from cpe_flasher.core import prepare_flash
        project = Path(__file__).resolve().parent/'projects'/'cpe-series-2-ortain'
        plan = prepare_flash(self.fixture.archive, self.fixture.target, self.fixture.root/'stage', self.fixture.source,
                             project, Path('python'), lambda _:None, self.fixture.compiler, self.fixture.options)
        self.assertEqual(json.loads((plan.portable/'cpe-flash-profile.json').read_text())['loading_preset'], 'ortain')
        self.assertTrue((plan.portable/'cpe_project'/'engine.py').is_file())
