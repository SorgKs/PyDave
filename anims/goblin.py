#!/usr/bin/env python3
"""anims/goblin.py — Гоблин: быстрый враг."""
from anims import register_object_type

HITBOX = (14, 28)
ANCHOR_TYPE = 'ground'
LAYER = 2
NAME = 'goblin'

def init(obj, params):
    obj['speed'] = 0.6
    return ['goblin_walk1', 'goblin_walk2', 'goblin_run1', 'goblin_run2']

def behave(obj, input_data, ctx):
    if ctx is None:
        return
    obj['vy'] = min(7, obj['vy'] + 0.5)
    obj['x'] += obj.get('vx', 0)
    obj['y'] += obj['vy']
    obj['onG'] = False
    gy = int((obj['y'] + obj['h'] + 2) // ctx.TS)
    gx = int(obj['x'] // ctx.TS)
    if 0 <= gy < ctx.ROWS and ctx.grid[gy][gx] in (1, 2):
        if obj['vy'] >= 0:
            obj['y'] = gy * ctx.TS - obj['h']
            obj['vy'] = 0
            obj['onG'] = True

def transform(obj):
    obj['collisions'] = []

def get_sprite(obj):
    return 'goblin_walk1'

register_object_type(
    name=NAME,
    init_func=init,
    behave_func=behave,
    transform_func=transform,
    get_sprite_func=get_sprite,
    hitbox=HITBOX,
    anchor_type=ANCHOR_TYPE,
    layer=LAYER,
    tags=['enemy', 'damage'],
)
