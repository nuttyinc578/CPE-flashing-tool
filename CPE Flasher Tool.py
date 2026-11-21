from cpe_flasher.gui import main
import json
import sys
from pathlib import Path

if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--self-test':
        from cpe_flasher.gui import FlasherApp
        from cpe_flasher import __version__
        from cpe_flasher.core import source_root
        import tempfile
        temporary = tempfile.TemporaryDirectory()
        app = FlasherApp(show_warning=False, slot_file=Path(temporary.name)/'slots.json')
        app.withdraw()
        app.update_idletasks()
        source_root(Path(app.source.get()))
        initial_cube_slots = sum(check.get() for check in app.cube_slot_checks)
        app.cube_slots[0].set('first-test.tar')
        app.cube_slots[-1].set('last-test.tar')
        app.cube_slot_buttons[-1].invoke()
        app.plan = object()
        app.cube_slot_buttons[0].invoke()
        switching_cleared_plan = app.plan is None
        multiple_cube_slots = [slot for slot, _ in app.selected_cube_overlays()]
        app.uncheck_cube_slots()
        uncheck_cleared_selection = not app.selected_cube_overlays()
        app.use_build_mode_slot()
        build_mode_selection = app.selected_cube_overlays() == ((2, app.build_mode_tar),) and app.build_mode_tar.is_file()
        app.uncheck_cube_slots()
        Path(sys.argv[2]).write_text(json.dumps({'version': __version__, 'gui_initialized': True, 'rebuild_source_present': True, 'controls': len(app.controls),
                                               'christmas_countdown':app.christmas_clock.get(),
                                               'game_profiles':sorted(p.stem for p in (Path(getattr(sys,'_MEIPASS','.'))/'game-versions').glob('*.zip')),
                                               'custom_cube_slots': len(app.cube_slots),
                                               'custom_cube_active_default': initial_cube_slots,
                                               'custom_cube_multiple': multiple_cube_slots,
                                               'custom_cube_uncheck_all': uncheck_cleared_selection,
                                               'custom_cube_build_mode': build_mode_selection,
                                               'custom_cube_switch_invalidates_plan': switching_cleared_plan,
                                               'tabs': len(app.notebook.tabs()), 'update_override_default': app.allow_unlocked_updates.get(),
                                               'custom_portable_default': app.custom_portable.get(),
                                               'custom_files_default': app.allow_custom_files.get(),
                                               'old_portable_restrictions_removed_default': app.remove_old_portable_restrictions.get(),
                                               'source_selection_fix': callable(getattr(app, 'use_bundled_source', None)),
                                               'custom_sha_empty': not app.custom_portable_sha256.get(),
                                               'custom_exe_names_empty': not app.custom_executable_name.get() and not app.target_executable_name.get(),
                                               'python_discovery_patch': (Path(getattr(sys, '_MEIPASS', '.'))/'flashing.patch').is_file(),
                                               'detected_python': app.python.get(),
                                               'custom_cube_bundle': (Path(getattr(sys, '_MEIPASS', '.'))/'Custom-Cube-Beta-Ortain.tar').is_file()
                                               and (Path(getattr(sys, '_MEIPASS', '.'))/'projects'/'cpe-series-2-ortain'/'cpe-project.json').is_file()}), encoding='utf-8')
        app.destroy()
        temporary.cleanup()
    else: main()
