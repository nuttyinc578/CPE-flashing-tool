from cpe_flasher.gui import main
import json
import sys
from pathlib import Path

if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--self-test':
        from cpe_flasher.gui import FlasherApp
        from cpe_flasher.core import source_root
        app = FlasherApp(show_warning=False)
        app.withdraw()
        app.update_idletasks()
        source_root(Path(app.source.get()))
        Path(sys.argv[2]).write_text(json.dumps({'gui_initialized': True, 'rebuild_source_present': True, 'controls': len(app.controls),
                                               'tabs': len(app.notebook.tabs()), 'update_override_default': app.allow_unlocked_updates.get(),
                                               'python_discovery_patch': (Path(getattr(sys, '_MEIPASS', '.'))/'flashing.patch').is_file(),
                                               'detected_python': app.python.get(),
                                               'custom_cube_bundle': (Path(getattr(sys, '_MEIPASS', '.'))/'Custom-Cube-Beta-Ortain.tar').is_file()
                                               and (Path(getattr(sys, '_MEIPASS', '.'))/'projects'/'cpe-series-2-ortain'/'cpe-project.json').is_file()}), encoding='utf-8')
        app.destroy()
    else: main()
