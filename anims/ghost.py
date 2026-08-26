#!/usr/bin/env python3
"""anims/ghost.py — летающий враг (без гравитации)."""
from anims import register_object_type, LAYER_ENEMY

HITBOX = (1.25, 1.5)
SPEED = 0.02


def sprites_map():
    # glow_ghost — опциональный файл; ключ для свечения в main при наличии
    return {
        'ghost1': 'ghost1.bmp',
        'ghost2': 'ghost2.bmp',
        'glow_ghost': 'glow_ghost.bmp',
    }


def init(obj, params):
    obj['speed'] = SPEED
    obj['vx'] = SPEED
    obj['has_gravity'] = False
    obj['has_friction'] = False
    obj['hp'] = (params or {}).get('hp', 2)
    obj['triggers'] = []
    obj['dead'] = False


def behave(obj, keys, map_grid, objects_list=None):
    if obj.get('dead'):
        obj['vx'] = 0
        obj['vy'] = 0
        return
    phase = (obj.get('t', 0) % 40) - 20
    obj['vy'] = max(-0.12, min(0.12, phase * 0.005))
    if obj.get('hitW'):
        obj['face'] = -obj['face']
        obj['vx'] = obj['face'] * abs(obj.get('speed', SPEED))
    else:
        obj['vx'] = obj['face'] * abs(obj.get('speed', SPEED))


def transform(obj):
    for tr in obj.get('triggers', []):
        if isinstance(tr, dict) and tr.get('name') == 'get_shot':
            dmg = tr.get('damage', 1)
            obj['hp'] = obj.get('hp', 1) - dmg
            obj['flash'] = 12
            if obj['hp'] <= 0:
                obj['dead'] = True
    obj['triggers'] = []
    obj['collisions'] = []
    if obj.get('dead'):
        return None
    frame = 'ghost1' if (obj.get('t', 0) // 10) % 2 == 0 else 'ghost2'
    return frame


register_object_type(
    name='ghost',
    init_func=init,
    behave_func=behave,
    transform_func=transform,
    sprites_map_func=sprites_map,
    hitbox=HITBOX,
    anchor_type='center',
    layer=LAYER_ENEMY,
    tags=['enemy', 'damage', 'flying'],
    has_gravity=False,
    has_friction=False,
)
