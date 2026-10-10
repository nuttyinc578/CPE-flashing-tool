"""Compile our bundled Ortain example in an isolated, fresh build directory."""
import sys
from pathlib import Path
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
from cpeloader import write_json
from cpe_flasher.core import stage_source, apply_project, apply_options, compile_game, FlashOptions
from cpe_flasher.custom_cube import stage_custom_cube

workspace = root/'build'/'ortain-game-check'
workspace.mkdir(exist_ok=False)
build = workspace/'source'
portable = workspace/'portable'; portable.mkdir()
userdata = workspace/'userdata'; userdata.mkdir()
write_json(userdata/'userdata.json', {'schema':1, 'player_name':'Ortain QA'})
stage_source(root/'build'/'flasher-source', build)
apply_project(root/'projects'/'cpe-series-2-ortain', build, portable)
apply_options(FlashOptions(userdata), build, portable)
stage_custom_cube(root/'release-download'/'Custom-Cube-Beta-Ortain.tar', build, portable, workspace)
print(compile_game(build, Path(sys.executable), print))
