import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from nuttymod_root_support import open_security_menu, root_settings_screen, validate_settings


class RootSecurityTests(unittest.TestCase):
    def test_calls_existing_door_without_unlocking_or_recovering_automatically(self):
        app = SimpleNamespace(security_door=Mock(), cpeloader=Mock(), og_recovery=Mock())
        self.assertIn('Returned', open_security_menu(app))
        app.security_door.assert_called_once_with()
        self.assertEqual(app.cpeloader.mock_calls, [])
        self.assertEqual(app.og_recovery.mock_calls, [])

    def test_old_game_without_door_shows_a_message(self):
        self.assertIn('unavailable', open_security_menu(SimpleNamespace()))

    def test_settings_button_dispatch_and_return(self):
        import pygame
        pygame.init()
        screen = pygame.display.set_mode((1100,720))
        font = pygame.font.Font(None, 22)
        app = SimpleNamespace(screen=screen, large=font, small=font, tiny=font,
            clock=Mock(), common_events=lambda events: True, security_door=Mock(),
            nuttymod_root_settings=validate_settings({'schema':1}))
        click = pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=(290,533))
        escape = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        try:
            with patch('pygame.event.get', side_effect=[[click], [escape]]), patch('pygame.display.flip'):
                root_settings_screen(app)
            app.security_door.assert_called_once_with()
            self.assertFalse(app._nuttymod_root_menu_open)
        finally: pygame.quit()


if __name__ == '__main__': unittest.main()
