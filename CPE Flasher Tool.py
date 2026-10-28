from cpe_flasher.gui import main
import json
import sys
from pathlib import Path

if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--self-test':
        from cpe_flasher.gui import FlasherApp
        from cpe_flasher import __version__
        from cpe_flasher.core import source_root
        app = FlasherApp(show_warning=False)
        app.withdraw()
        app.update_idletasks()
        source_root(Path(app.source.get()))
        Path(sys.argv[2]).write_text(json.dumps({'version': __version__, 'gui_initialized': True, 'rebuild_source_present': True, 'controls': len(app.controls),
                                               'tabs': len(app.notebook.tabs()), 'update_override_default': app.allow_unlocked_updates.get(),
                                               'custom_portable_default': app.custom_portable.get(),
                                               'custom_files_default': app.allow_custom_files.get(),
                                               'old_portable_restrictions_removed_default': app.remove_old_portable_restrictions.get(),
                                               'custom_sha_empty': not app.custom_portable_sha256.get(),
                                               'custom_exe_names_empty': not app.custom_executable_name.get() and not app.target_executable_name.get(),
                                               'python_discovery_patch': (Path(getattr(sys, '_MEIPASS', '.'))/'flashing.patch').is_file(),
                                               'detected_python': app.python.get(),
                                               'custom_cube_bundle': (Path(getattr(sys, '_MEIPASS', '.'))/'Custom-Cube-Beta-Ortain.tar').is_file()
                                               and (Path(getattr(sys, '_MEIPASS', '.'))/'projects'/'cpe-series-2-ortain'/'cpe-project.json').is_file()}), encoding='utf-8')
        app.destroy()
    else: main()
