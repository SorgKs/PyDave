#!/usr/bin/env python3
"""anims/item_gem.py — подбираемый кристалл."""
from anims import register_object_type, LAYER_ITEM

HITBOX = (1.0, 1.0)


def sprites_map():
    return {'gem': 'gem.bmp'}


def init(obj, params):
    obj['taken'] = False
    obj['seed'] = (params or {}).get('seed', 0.0)
    obj['has_gravity'] = True
    obj['has_friction'] = True


def behave(obj, keys, map_grid, objects_list=None):
    pass


def transform(obj):
    for col in obj.get('collisions', []):
        if col.get('kind') != 'object':
            continue
        target = col.get('target')
        if target and 'player' in target.get('tags', []):
            obj['taken'] = True
    obj['collisions'] = []
    if obj.get('taken'):
        return None
    return 'gem'


register_object_type(
    name='item_gem',
    init_func=init,
    behave_func=behave,
    transform_func=transform,
    sprites_map_func=sprites_map,
    hitbox=HITBOX,
    anchor_type='center',
    layer=LAYER_ITEM,
    tags=['collectible', 'item'],
    has_gravity=True,
    has_friction=True,
)
