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
        Path(sys.argv[2]).write_text(json.dumps({'gui_initialized': True, 'rebuild_source_present': True, 'controls': len(app.controls)}), encoding='utf-8')
        app.destroy()
    else: main()
