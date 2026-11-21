"""Build Mode: grid-snapped CPE pieces and fixed beams in solo play."""
import math
import pygame

GRID = 32
MAX_PIECES = 120
BEAM_HALF_LENGTH = 45
BEAM_RADIUS = 7
GLOW = (134, 239, 218)
TOOLS = ('Block', 'Ball', 'Beam')


class BuildMode:
    def __init__(self, app):
        from cube_core import FLOOR_Y, WIDTH, ShapeSpec, pymunk

        self.app = app
        self.floor = FLOOR_Y
        self.width = WIDTH
        self.physics = pymunk
        self.shape_spec = ShapeSpec
        self.button = pygame.Rect(WIDTH - 352, 14, 166, 36)
        self.enabled = False
        self.tool = 0
        self.vertical = False
        self.pieces = []
        self.world = None
        self.base_events = app.common_events
        self.base_dispatch = app.dispatch_action
        self.base_hud = app.draw_game_hud

    def toggle(self):
        self.enabled = not self.enabled
        if self.enabled and self.world is not None:
            self.world.end_drag('host')
        self.app.play_click()

    def events(self, events):
        if not self.base_events(events):
            return False
        for event in list(events):
            if (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                    and self.button.collidepoint(event.pos)):
                self.toggle()
            elif event.type != pygame.KEYDOWN:
                continue
            elif event.key == pygame.K_b:
                if not getattr(event, 'repeat', False):
                    self.toggle()
            elif not self.enabled:
                continue
            elif event.key == pygame.K_ESCAPE:
                self.enabled = False
            elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                self.tool = event.key - pygame.K_1
            elif event.key == pygame.K_r:
                self.vertical = not self.vertical
            elif event.key == pygame.K_z:
                self.undo()
            else:
                continue
            events.remove(event)
        return True

    def within_grid(self, point):
        x, y = point
        return 30 <= x < self.width - 30 and 150 <= y < self.floor - 15

    def snap(self, point):
        x, y = point
        return (max(GRID * 2, min((self.width - 64) // GRID * GRID, round(x / GRID) * GRID)),
                max(GRID * 5, min((self.floor - 64) // GRID * GRID, round(y / GRID) * GRID)))

    def endpoints(self, center):
        x, y = center
        d = BEAM_HALF_LENGTH
        return ((x, y - d), (x, y + d)) if self.vertical else ((x - d, y), (x + d, y))

    def place(self, world, point):
        if not self.within_grid(point):
            return
        self.pieces[:] = [p for p in self.pieces if p[0] == 'beam' or p[1] in world.entities]
        if len(self.pieces) >= MAX_PIECES:
            self.app.notify('Build Mode limit reached. Undo a piece or clear the sandbox.')
            return
        center = self.snap(point)
        if self.tool == 2:
            ends = self.endpoints(center)
            # Rephysics treats segments as world boundaries. A finite static
            # polygon works as a platform on both backends.
            body_type = getattr(self.physics.Body, 'STATIC', None)
            body = self.physics.Body() if body_type is None else self.physics.Body(body_type=body_type)
            body.position = center
            wide, narrow = BEAM_HALF_LENGTH, BEAM_RADIUS
            w, h = (narrow, wide) if self.vertical else (wide, narrow)
            shape = self.physics.Poly(body, [(-w, -h), (w, -h), (w, h), (-w, h)])
            shape.friction = 0.95
            shape.elasticity = 0.28
            world.space.add(body, shape)
            self.pieces.append(('beam', shape, ends))
        else:
            block = self.tool == 0
            spec = self.shape_spec('Build Block' if block else 'Build Ball',
                                   'polygon' if block else 'circle', 4 if block else 0, 27)
            entity = world.spawn(*center, owner='host', spec=spec, color=GLOW)
            if block:
                entity.body.angle = math.pi / 4
            self.pieces.append(('body', entity.entity_id, None))
        self.world = world

    def undo(self):
        if self.world is None:
            return
        while self.pieces:
            kind, item, _ = self.pieces.pop()
            if kind == 'beam':
                self.world.space.remove(item, item.body)
                return
            if item in self.world.entities:
                self.world.remove(item)
                return

    def clear_beams(self):
        if self.world is not None:
            for kind, item, _ in self.pieces:
                if kind == 'beam':
                    self.world.space.remove(item, item.body)
        self.pieces.clear()

    def dispatch(self, action, peer, is_host, world, events):
        if world is not None:
            self.world = world
        name = action.get('action')
        if name == 'clear':
            self.clear_beams()
        elif self.enabled and world is not None:
            if name in {'spawn', 'drag_start'}:
                world.end_drag('host')
                self.place(world, (action['x'], action['y']))
                return
            if name == 'drag_move':
                return
        return self.base_dispatch(action, peer, is_host, world, events)

    def draw_hud(self, *args, **kwargs):
        screen = self.app.screen
        for kind, _, ends in self.pieces:
            if kind == 'beam':
                pygame.draw.line(screen, (19, 48, 66), *ends, BEAM_RADIUS * 2)
                pygame.draw.line(screen, GLOW, *ends, 2)
        if self.enabled:
            grid = (67, 92, 108)
            for x in range(GRID * 2, self.width - 32, GRID):
                pygame.draw.line(screen, grid, (x, GRID * 5), (x, self.floor - 15))
            for y in range(GRID * 5, self.floor - 15, GRID):
                pygame.draw.line(screen, grid, (GRID * 2, y), (self.width - 32, y))
            mouse = pygame.mouse.get_pos()
            if self.within_grid(mouse):
                x, y = self.snap(mouse)
                if self.tool == 2:
                    pygame.draw.line(screen, GLOW, *self.endpoints((x, y)), 3)
                elif self.tool == 1:
                    pygame.draw.circle(screen, GLOW, (x, y), 27, 2)
                else:
                    pygame.draw.rect(screen, GLOW, (x - 19, y - 19, 38, 38), 2)
        self.base_hud(*args, **kwargs)
        pygame.draw.rect(screen, (30, 67, 78) if self.enabled else (24, 48, 63), self.button, border_radius=9)
        pygame.draw.rect(screen, GLOW, self.button, 2, border_radius=9)
        label = self.app.small.render('Build ON [B]' if self.enabled else 'Build Mode [B]', True, GLOW)
        screen.blit(label, label.get_rect(center=self.button.center))
        if self.enabled:
            help_text = f'{TOOLS[self.tool]} selected  |  1 Block   2 Ball   3 Beam   R Rotate beam   Z Undo   Esc Exit'
            strip = self.app.small.render(help_text, True, GLOW)
            rect = strip.get_rect(midleft=(18, self.floor + 23))
            pygame.draw.rect(screen, (18, 37, 51), rect.inflate(16, 9), border_radius=7)
            screen.blit(strip, rect)


def on_load(app, userdata):
    # The trusted startup hook is only enabled by the flashed game profile.
    if not getattr(app, 'game_root_enabled', False) or getattr(app, '_cube_build_mode_installed', False):
        return
    base_play = app.run_simulation

    def play(peer=None, is_host=True):
        if peer is not None:
            return base_play(peer, is_host)
        build = BuildMode(app)
        app.common_events = build.events
        app.dispatch_action = build.dispatch
        app.draw_game_hud = build.draw_hud
        try:
            return base_play(peer, is_host)
        finally:
            app.common_events = build.base_events
            app.dispatch_action = build.base_dispatch
            app.draw_game_hud = build.base_hud

    app.run_simulation = play
    app._cube_build_mode_installed = True
