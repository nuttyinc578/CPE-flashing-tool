from datetime import timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from cpe_flasher import __version__
from cpe_flasher.core import FlasherError, select_executable, find_portable, prepare_flash
from cpe_flasher.releases import CHRISTMAS_DATE, CHRISTMAS, NIGHTLY, HALLOWEEN, SUPPORTED, countdown, source_version
from cpeloader import CPELoader, COMPONENTS, snapshot, write_json
import test_cpe_flasher as fixtures

class Profiles(unittest.TestCase):
    def test_schedule(self):
        self.assertEqual(__version__,'1.2.5')
        self.assertIn('1d 00:00:01',countdown(CHRISTMAS_DATE-timedelta(days=1,seconds=1)))
        self.assertIn('0d 00:00:01',countdown(CHRISTMAS_DATE-timedelta(microseconds=1)))
        for d in (0,30):
            self.assertIn('Check official releases',countdown(CHRISTMAS_DATE+timedelta(days=d)))
    def test_current_and_future_layouts(self):
        for version,game in zip(SUPPORTED,(HALLOWEEN,HALLOWEEN,NIGHTLY,CHRISTMAS)):
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
