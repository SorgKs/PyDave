#!/usr/bin/env python3
"""anims/ghost.py — Призрак: летающий враг."""
from anims import register_object_type

HITBOX = (20, 24)
ANCHOR_TYPE = 'center'
LAYER = 2
NAME = 'ghost'

def init(obj, params):
    obj['speed'] = 0.3
    obj['has_gravity'] = False
    return ['ghost1', 'ghost2', 'glow_ghost']

def behave(obj, input_data, ctx):
    if ctx is None:
        return
    # Лёгкое парение
    obj['vy'] = min(2, max(-2, obj['vy'] + 0.1 * (obj.get('t', 0) % 10 - 5)))
    obj['x'] += obj.get('vx', 0)
    obj['y'] += obj['vy']

def transform(obj):
    obj['collisions'] = []

def get_sprite(obj):
    return 'ghost1'

register_object_type(
    name=NAME,
    init_func=init,
    behave_func=behave,
    transform_func=transform,
    get_sprite_func=get_sprite,
    hitbox=HITBOX,
    anchor_type=ANCHOR_TYPE,
    layer=LAYER,
    tags=['enemy', 'damage', 'flying'],
)
