import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
root = Path(__file__).resolve().parent
sys.path.insert(0, str(root/'projects'/'cpe-series-2-ortain'))
sys.path.append(str(root/'build'/'flasher-source'))
from cpe_project import CubePhysicsEngine


class OrtainTests(unittest.TestCase):
    def test_motion_trails_pause_and_particle_cap(self):
        engine = CubePhysicsEngine(gravity=(0,0), particle_limit=8, particle_seed=1)
        body = engine.spawn('box', 200, 150, 16, 1, (100,200,255))
        engine.particles.clear()
        engine.bodies[body].body.velocity = (150,0)
        engine.step(.1)
        self.assertGreater(len(engine.particles.particles), 0)
        self.assertLessEqual(len(engine.particles.particles), 8)
        engine.particles.clear(); engine.paused = True
        engine.step(.1)
        self.assertEqual(len(engine.particles.particles), 0)
        self.assertEqual(engine.snapshot()['backend'], 'series-2-ortain')

    def test_pulse_pushes_nearby_bodies(self):
        engine = CubePhysicsEngine(gravity=(0,0), particle_seed=1)
        body = engine.spawn('box', 220, 150, 16, 1, (100,200,255))
        self.assertEqual(engine.pulse(200,150), 1)
        self.assertGreater(engine.bodies[body].body.velocity.x, 0)
        self.assertEqual(engine.health_report()['project_version'], '2.0.0')

    def test_loading_scene_finishes_or_honors_quit(self):
        import pygame
        from game_overrides.custom_cube_loading import ortain_loading
        pygame.init()
        app = SimpleNamespace(screen=pygame.Surface((1100,720)), large=pygame.font.Font(None,46),
                              small=pygame.font.Font(None,24), clock=SimpleNamespace(tick=lambda _:None),
                              common_events=lambda events:True)
        with patch('pygame.display.flip'), patch('pygame.event.get', return_value=[]), patch('game_overrides.custom_cube_loading.time.monotonic', side_effect=[0,1,3]):
            self.assertTrue(ortain_loading(app))
        app.common_events=lambda events:False
        with patch('pygame.event.get', return_value=[]): self.assertFalse(ortain_loading(app))
        pygame.quit()
