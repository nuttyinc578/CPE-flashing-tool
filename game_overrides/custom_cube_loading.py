"""Ortain loading scene; required loader/integrity prompts run first."""
import math
import time
import pygame


def draw_frame(app, progress, seconds):
    width, height = app.screen.get_size()
    app.screen.fill((8, 12, 26))
    for x in range(0, width, 55): pygame.draw.line(app.screen, (18, 29, 47), (x, 0), (x, height))
    for y in range(0, height, 55): pygame.draw.line(app.screen, (18, 29, 47), (0, y), (width, y))
    center = (width//2, height//2-60)
    pygame.draw.circle(app.screen, (55, 72, 111), center, 115, 1)
    for index in range(8):
        angle = seconds*.7+index*math.tau/8
        point = (int(center[0]+math.cos(angle)*115), int(center[1]+math.sin(angle)*115))
        pygame.draw.rect(app.screen, (100, 230, 255), (point[0]-6, point[1]-6, 12, 12), border_radius=2)
    pygame.draw.rect(app.screen, (174, 133, 255), (center[0]-24, center[1]-24, 48, 48), width=3, border_radius=8)
    for font, text, y, color in ((app.large, 'CPE SERIES 2', 100, (231, 240, 255)),
                                (app.small, 'ORTAIN / INDEPENDENT PHYSICS + IPE', 155, (100, 230, 255)),
                                (app.small, 'Motion trails / pulse field / custom cubes', height-155, (174, 190, 218)),
                                (app.small, f'INITIALIZING {int(progress*100)}%', height-75, (231, 240, 255))):
        label = font.render(text, True, color)
        app.screen.blit(label, label.get_rect(center=(width//2, y)))
    bar = pygame.Rect(width//5, height-120, width*3//5, 12)
    pygame.draw.rect(app.screen, (32, 42, 67), bar, border_radius=6)
    pygame.draw.rect(app.screen, (100, 230, 255), (bar.x, bar.y, int(bar.width*progress), bar.height), border_radius=6)


def ortain_loading(app):
    started = time.monotonic()
    while True:
        events = pygame.event.get()
        if not app.common_events(events): return False
        elapsed = time.monotonic()-started
        progress = min(1.0, elapsed/2.4)
        draw_frame(app, progress, elapsed)
        pygame.display.flip()
        app.clock.tick(60)
        if progress >= 1: return True
