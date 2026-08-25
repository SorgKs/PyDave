#!/usr/bin/env python3
"""anims/skull.py — Череп: статичный декоративный объект."""
from anims import register_object_type

HITBOX = (16, 16)
ANCHOR_TYPE = 'center'
LAYER = 0
NAME = 'skull'

def init(obj, params):
    return ['skull']

def behave(obj, input_data, ctx):
    pass

def transform(obj):
    obj['collisions'] = []

def get_sprite(obj):
    return 'skull'

register_object_type(
    name=NAME,
    init_func=init,
    behave_func=behave,
    transform_func=transform,
    get_sprite_func=get_sprite,
    hitbox=HITBOX,
    anchor_type=ANCHOR_TYPE,
    layer=LAYER,
    tags=['decoration'],
)
