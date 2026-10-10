"""Edit this hook or add root-level Python source overlays to the package."""
def on_load(app, userdata):
    import pygame
    pygame.display.set_caption('The Cube Beta — Custom Ortain Edition')
    app.custom_cube_name = 'Custom Ortain Edition'
    app.custom_cube_enabled = True
    import cube_core
    cube_core.FALL_PALETTE = ((102,235,255), (174,133,255), (255,124,202), (132,255,205))
    world_type = cube_core.PhysicsWorld
    if not getattr(world_type, '_custom_ortain_spawn', False):
        original = world_type.spawn
        def spawn(world, *args, **kwargs):
            entity = original(world, *args, **kwargs)
            if hasattr(world.cpe, 'pulse'):
                world.cpe.pulse(entity.body.position.x, entity.body.position.y, radius=160, strength=100)
            return entity
        world_type.spawn = spawn
        world_type._custom_ortain_spawn = True
