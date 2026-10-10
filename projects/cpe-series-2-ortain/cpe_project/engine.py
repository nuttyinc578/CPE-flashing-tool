"""Ortain: bounded neon motion trails and a radial pulse API."""
import math
from cpe_rephysics.engine import CubePhysicsEngine as RephysicsEngine


class CubePhysicsEngine(RephysicsEngine):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.motion_trails = True
        self._trail_timer = 0.0

    def step(self, dt):
        super().step(dt)
        if self.paused or not self.motion_trails: return
        self._trail_timer += max(0.0, min(float(dt), .25))
        if self._trail_timer < .08: return
        self._trail_timer = 0.0
        for record in list(self.bodies.values())[:24]:
            if record.body.velocity.length > 90:
                p = record.body.position
                self.particles.emit(p.x, p.y, 2, 35, .28, (102, 235, 255), 2)

    def pulse(self, x, y, radius=220, strength=280):
        radius = max(1, min(800, float(radius)))
        strength = max(0, min(1200, float(strength)))
        affected = 0
        for record in self.bodies.values():
            dx, dy = record.body.position.x-x, record.body.position.y-y
            distance = math.hypot(dx, dy)
            if 0 < distance < radius:
                magnitude = strength*(1-distance/radius)*record.body.mass
                record.body.apply_impulse_at_local_point((dx/distance*magnitude, dy/distance*magnitude))
                affected += 1
        self.particles.emit(x, y, 36, 230, .65, (172, 126, 255), 3)
        return affected

    def snapshot(self):
        result = super().snapshot()
        result.update(backend='series-2-ortain', series=2, motion_trails=self.motion_trails)
        return result

    def health_report(self):
        result = super().health_report()
        result.update(backend='series-2-ortain', project='CPE Series 2 — Ortain', project_version='2.0.0')
        return result
