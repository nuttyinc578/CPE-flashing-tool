import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from cpe_flasher.cube_slots import BUNDLED_ORTAIN, SLOT_COUNT, load_slots, save_slots, selected_tar
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
        for i, path in enumerate(paths, 1):
            self.assertEqual(selected_tar(paths,i,Path('bundled.tar')),Path(path))
        self.assertIsNone(selected_tar(paths,0,Path('bundled.tar')))

    def test_corrupt_profiles_do_not_enable_overlay(self):
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp)/'slots.json'
            file.write_text('not JSON',encoding='utf-8')
            self.assertEqual(load_slots(file),('',)*SLOT_COUNT)
            file.write_text(json.dumps({'schema':1,'paths':['hi.tar',None,3]}),encoding='utf-8')
            self.assertEqual(load_slots(file),('hi.tar','','','','',''))
        with self.assertRaisesRegex(ValueError,'Slot 6 is empty'):
            selected_tar(('',)*6,6,Path('bundled.tar'))

    def test_bundled_ortain_resolves_to_current_app_not_old_extract_folder(self):
        paths=('',)*5+(BUNDLED_ORTAIN,)
        self.assertEqual(selected_tar(paths,6,Path('current-bundle/ortain.tar')),Path('current-bundle/ortain.tar'))

    def test_browse_and_clear_one_slot_without_changing_other_paths(self):
        values=[Variable(f'old-{i}.tar') for i in range(6)]
        app=SimpleNamespace(cube_slots=values,active_cube_slot=Variable(1))
        with patch('cpe_flasher.gui.filedialog.askopenfilename',return_value='my-new.tar'):
            FlasherApp.pick_cube_slot(app,6)
        self.assertEqual(app.active_cube_slot.get(),6)
        self.assertEqual(values[5].get(),'my-new.tar')
        FlasherApp.clear_cube_slot(app,6)
        self.assertEqual(app.active_cube_slot.get(),0)
        self.assertEqual([v.get() for v in values],['old-0.tar','old-1.tar','old-2.tar','old-3.tar','old-4.tar',''])

    def test_prepare_passes_only_selected_tar_to_flash_and_names_it(self):
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
        app.active_cube_slot=Variable(6)
        app.ortain_tar=Path('bundled.tar')
        app.cube_slot_paths=lambda: ('one.tar','two.tar','three.tar','four.tar','five.tar','six.tar')
        with patch('cpe_flasher.gui.prepare_flash') as prepare, patch('cpe_flasher.gui.messagebox.askyesno',return_value=True) as confirm:
            FlasherApp.prepare(app)
            self.assertEqual(prepare.call_args.kwargs['options'].custom_cube_tar,Path('six.tar'))
            self.assertIn('slot 6: six.tar',confirm.call_args.args[1])
            self.assertNotIn('one.tar',confirm.call_args.args[1])
