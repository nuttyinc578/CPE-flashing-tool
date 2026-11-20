import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from cpe_flasher.cube_slots import BUNDLED_ORTAIN, SLOT_COUNT, load_slots, save_slots, selected_tars
from cpe_flasher.gui import FlasherApp


class Variable:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class CubeSlotTests(unittest.TestCase):
    def test_all_six_paths_roundtrip_without_saved_selection(self):
        paths = tuple(f'C:/My Custom Cubes/Player {i}.tar' for i in range(1,7))
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp)/'prefs'/'slots.json'
            self.assertEqual(load_slots(file), ('',)*6)
            save_slots(file, paths)
            self.assertEqual(load_slots(file), paths)
            self.assertNotIn('active', json.loads(file.read_text(encoding='utf-8')))
        self.assertEqual(selected_tars(paths, (True,)*6, Path('bundled.tar')),
                         tuple((slot, Path(path)) for slot, path in enumerate(paths, 1)))
        self.assertEqual(selected_tars(paths, (False,)*6, Path('bundled.tar')), ())

    def test_corrupt_profiles_do_not_enable_overlay(self):
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp)/'slots.json'
            file.write_text('not JSON',encoding='utf-8')
            self.assertEqual(load_slots(file),('',)*SLOT_COUNT)
            file.write_text(json.dumps({'schema':1,'paths':['hi.tar',None,3]}),encoding='utf-8')
            self.assertEqual(load_slots(file),('hi.tar','','','','',''))
        with self.assertRaisesRegex(ValueError,'Slot 6 is empty'):
            selected_tars(('',)*6, (False,)*5+(True,), Path('bundled.tar'))

    def test_bundled_ortain_resolves_to_current_app_not_old_extract_folder(self):
        paths=('',)*5+(BUNDLED_ORTAIN,)
        self.assertEqual(selected_tars(paths, (False,)*5+(True,), Path('current-bundle/ortain.tar')),
                         ((6, Path('current-bundle/ortain.tar')),))

    def test_browse_and_clear_one_slot_without_changing_other_paths(self):
        values=[Variable(f'old-{i}.tar') for i in range(6)]
        flags = [Variable(i == 0) for i in range(6)]
        app=SimpleNamespace(cube_slots=values,cube_slot_checks=flags)
        with patch('cpe_flasher.gui.filedialog.askopenfilename',return_value='my-new.tar'):
            FlasherApp.pick_cube_slot(app,6)
        self.assertTrue(flags[0].get())
        self.assertTrue(flags[5].get())
        self.assertEqual(values[5].get(),'my-new.tar')
        FlasherApp.clear_cube_slot(app,6)
        self.assertFalse(flags[5].get())
        self.assertTrue(flags[0].get())
        self.assertEqual([v.get() for v in values],['old-0.tar','old-1.tar','old-2.tar','old-3.tar','old-4.tar',''])

    def test_ortain_fills_empty_slot_without_replacing_checked_packages(self):
        values = [Variable('my-game.tar'), *[Variable('') for _ in range(5)]]
        flags = [Variable(i == 0) for i in range(6)]
        app = SimpleNamespace(cube_slots=values, cube_slot_checks=flags)
        app.cube_slot_paths = lambda: FlasherApp.cube_slot_paths(app)
        FlasherApp.use_ortain_slot(app)
        FlasherApp.use_ortain_slot(app)
        self.assertEqual(app.cube_slot_paths(), ('my-game.tar', BUNDLED_ORTAIN, '', '', '', ''))
        self.assertEqual([flag.get() for flag in flags], [True, True, False, False, False, False])
        FlasherApp.uncheck_cube_slots(app)
        self.assertFalse(any(flag.get() for flag in flags))
        self.assertEqual(values[1].get(), BUNDLED_ORTAIN)

    def test_prepare_passes_checked_tars_in_slot_order_and_names_them(self):
        names = ('archive','target','python','userdata','source','project','loader','custom_portable_sha256',
                 'custom_executable_name','target_executable_name')
        app=SimpleNamespace(**{name:Variable('') for name in names})
        for name in ('archive','target','python','userdata'): getattr(app,name).set(name)
        for name in ('custom_portable','allow_custom_files','remove_old_portable_restrictions','allow_unlocked_updates','nuttyroot','verbose','safety_alerts'):
            setattr(app,name,Variable(False))
        app.trust=app.full_rewrite=Variable(True)
        app.status=Variable('')
        app.scripts=()
        app.bundled_source=''
        app.log=Mock()
        app.start=lambda work: work()
        app.cube_slot_checks=[Variable(i in {2,6}) for i in range(1,7)]
        app.ortain_tar=Path('bundled.tar')
        app.cube_slot_paths=lambda: ('one.tar','two.tar','three.tar','four.tar','five.tar','six.tar')
        app.selected_cube_overlays=lambda: FlasherApp.selected_cube_overlays(app)
        with patch('cpe_flasher.gui.prepare_flash') as prepare, patch('cpe_flasher.gui.messagebox.askyesno',return_value=True) as confirm:
            FlasherApp.prepare(app)
            self.assertEqual(prepare.call_args.kwargs['options'].custom_cube_tars, (Path('two.tar'), Path('six.tar')))
            self.assertIn('Slot 2: two.tar\nSlot 6: six.tar',confirm.call_args.args[1])
            self.assertNotIn('one.tar',confirm.call_args.args[1])
