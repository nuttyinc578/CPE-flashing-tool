import os
from pathlib import Path
import runpy
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')


class BuildModeTests(unittest.TestCase):
    def test_installation_requires_flashed_profile_and_leaves_multiplayer_untouched(self):
        import pygame
        hook = runpy.run_path(str(Path(__file__).parent/'build_mode_template/python/cube_build_mode.py'))['on_load']
        app = SimpleNamespace(game_root_enabled=False, common_events=Mock(return_value=True),
                              dispatch_action=Mock(), draw_game_hud=Mock(), play_click=Mock())
        original = (app.common_events, app.dispatch_action, app.draw_game_hud)
        seen = []

        def simulation(peer=None, is_host=True):
            seen.append((peer, app.common_events is original[0]))
            if peer is None:
                events = [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_b)]
                self.assertTrue(app.common_events(events))
                self.assertEqual(events, [])
            return 'menu'

        app.run_simulation = simulation
        hook(app, {})
        self.assertIs(app.run_simulation, simulation)
        app.game_root_enabled = True
        hook(app, {})
        installed = app.run_simulation
        hook(app, {})
        self.assertIs(app.run_simulation, installed)
        peer = object()
        core = SimpleNamespace(WIDTH=1100, FLOOR_Y=666, ShapeSpec=object, pymunk=object)
        with patch.dict(sys.modules, {'cube_core': core}):
            self.assertEqual(app.run_simulation(peer, False), 'menu')
            self.assertEqual(app.run_simulation(), 'menu')
        self.assertEqual(seen, [(peer, True), (None, False)])
        self.assertEqual((app.common_events, app.dispatch_action, app.draw_game_hud), original)
