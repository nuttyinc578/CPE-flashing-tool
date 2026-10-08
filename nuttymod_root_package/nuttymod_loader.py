"""Readable NuttyMod Root loader. No legacy Python .pyc or OS elevation."""

def on_load(app, userdata):
    from nuttymod_root_support import attach_root_settings
    attach_root_settings(app)
