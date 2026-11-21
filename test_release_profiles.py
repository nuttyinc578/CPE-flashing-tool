from datetime import timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import unittest
from unittest.mock import patch
from zipfile import ZipFile

from cpe_flasher import __version__
from cpe_flasher.core import FlasherError, select_executable, find_portable, pack_source, prepare_flash
from cpe_flasher.releases import CHRISTMAS_DATE, CHRISTMAS, NIGHTLY, HALLOWEEN, PROFILE_REVISIONS, SUPPORTED, countdown, source_version
from cpeloader import CPELoader, COMPONENTS, snapshot, write_json
import test_cpe_flasher as fixtures

class Profiles(unittest.TestCase):
    def test_schedule(self):
        self.assertEqual(__version__,'1.2.9')
        self.assertIn('1d 00:00:01',countdown(CHRISTMAS_DATE-timedelta(days=1,seconds=1)))
        self.assertIn('0d 00:00:01',countdown(CHRISTMAS_DATE-timedelta(microseconds=1)))
        for d in (0,30):
            self.assertIn('Check official releases',countdown(CHRISTMAS_DATE+timedelta(days=d)))
    def test_current_and_future_layouts(self):
        layouts = {
            '6.4.1': HALLOWEEN, '6.4.2': HALLOWEEN, '6.4.2-nightly': NIGHTLY,
            '6.4.3-nightly': NIGHTLY, '6.4.3-nightly.2': NIGHTLY, '6.4.3-nightly.3': NIGHTLY,
            '6.4.3': CHRISTMAS,
        }
        self.assertEqual(set(SUPPORTED), set(layouts))
        self.assertEqual(set(PROFILE_REVISIONS), set(layouts) - {'6.4.3'})
        for version,game in layouts.items():
            with self.subTest(version=version),TemporaryDirectory() as tmp:
                root=Path(tmp);sub=root/'nested';sub.mkdir()
                for n in (*COMPONENTS,'cpe.exe',game):(sub/n).write_bytes(b'fixture')
                write_json(sub/'cpeloader_manifest.json',{'files':snapshot(sub)})
                self.assertEqual(find_portable(root),sub)
                self.assertEqual(select_executable(sub),game)
                (sub/'Cube Beta PLUS.exe').touch()
                with self.assertRaisesRegex(FlasherError,'PLUS'):select_executable(sub)
    def test_stable_never_rebuilds_from_nightly(self):
        fx=fixtures.FlasherTests()
        fx.setUp();self.addCleanup(fx.tearDown)
        CPELoader(fx.target).unlock()
        (fx.source/'release_info.py').write_text("VERSION='6.4.3-nightly.2'")
        self.assertEqual(source_version(fx.source),'6.4.3-nightly.2')
        with patch('cpe_flasher.core.exe_version',return_value='6.4.3'),self.assertRaisesRegex(FlasherError,'does not match'):
            fx.prepare(compiler=lambda *_:self.fail('Must not compile'))

    def test_nightly_3_uses_only_its_matching_bundled_source(self):
        fx = fixtures.FlasherTests()
        fx.setUp(); self.addCleanup(fx.tearDown)
        CPELoader(fx.target).unlock()
        profiles = fx.root/'game-versions'
        profiles.mkdir()
        release = fx.source/'release_info.py'
        release.write_text("VERSION='6.4.3-nightly.2'", encoding='utf-8')
        pack_source(fx.source, profiles/'6.4.3-nightly.2.zip')
        release.write_text("VERSION='6.4.3-nightly.3'", encoding='utf-8')
        gallery = fx.source/'archive_assets'
        gallery.mkdir()
        (gallery/'10.png').write_bytes(b'screenshot')
        (gallery/'credentials.txt').write_bytes(b'not a build asset')
        pack_source(fx.source, profiles/'6.4.3-nightly.3.zip')

        def build(source, python, log):
            self.assertEqual(source_version(source), '6.4.3-nightly.3')
            self.assertEqual((source/'archive_assets'/'10.png').read_bytes(), b'screenshot')
            self.assertFalse((source/'archive_assets'/'credentials.txt').exists())
            return fx.compiler(source, python, log)

        with patch.object(sys, '_MEIPASS', str(fx.root), create=True):
            with patch('cpe_flasher.core.exe_version', side_effect=['6.4.3-nightly.3','6.4.3-nightly.2']):
                with self.assertRaisesRegex(FlasherError, 'Select a matching installation'):
                    prepare_flash(fx.archive, fx.target, fx.root/'mismatch', None, None,
                                  Path('python'), lambda _: None, lambda *_: self.fail('Must not compile'), fx.options)
            with patch('cpe_flasher.core.exe_version', return_value='6.4.3-nightly.3'):
                plan = prepare_flash(fx.archive, fx.target, fx.root/'stage', None, None,
                                     Path('python'), lambda _: None, build, fx.options)
        with ZipFile(plan.portable/'game-source.zip') as source:
            self.assertIn('archive_assets/10.png', source.namelist())
        self.assertEqual((fx.target/HALLOWEEN).read_bytes(), b'original game')
    def test_manifest_bytecode_must_match(self):
        import hashlib
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            for n in (*COMPONENTS,NIGHTLY):(root/n).write_bytes(b'test')
            name='addons/nuttymod/nuttymod_runtime_v122.pyc';p=root/name
            p.parent.mkdir(parents=True);p.write_bytes(b'original')
            write_json(root/'cpeloader_manifest.json',{'files':{**snapshot(root),name:hashlib.sha256(p.read_bytes()).hexdigest()}})
            self.assertEqual(find_portable(root),root)
            p.write_bytes(b'changed')
            with self.assertRaisesRegex(FlasherError,'integrity'):find_portable(root)
