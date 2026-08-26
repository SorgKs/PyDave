#!/usr/bin/env python3
"""anims/skull.py — декоративный объект."""
from anims import register_object_type, LAYER_NONE

HITBOX = (1.0, 1.0)


def sprites_map():
    return {'skull': 'skull.bmp'}


def init(obj, params):
    obj['has_gravity'] = False
    obj['has_friction'] = False


def behave(obj, keys, map_grid):
    pass


def transform(obj):
    obj['collisions'] = []
    return 'skull'


register_object_type(
    name='skull',
    init_func=init,
    behave_func=behave,
    transform_func=transform,
    sprites_map_func=sprites_map,
    hitbox=HITBOX,
    anchor_type='center',
    layer=LAYER_NONE,
    tags=['decoration'],
    has_gravity=False,
    has_friction=False,
)
