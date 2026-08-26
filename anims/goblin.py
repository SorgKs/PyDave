#!/usr/bin/env python3
"""anims/goblin.py — быстрый наземный враг."""
from anims import register_object_type, LAYER_ENEMY

HITBOX = (0.875, 1.75)  # 14×28 / 16
SPEED = 0.0375

ANIMS = {
    'walk': (['goblin_walk1', 'goblin_walk2', 'goblin_walk3', 'goblin_walk4'], 6),
}


def sprites_map():
    return {
        'goblin_walk1': 'goblin_walk1.bmp',
        'goblin_walk2': 'goblin_walk2.bmp',
        'goblin_walk3': 'goblin_walk3.bmp',
        'goblin_walk4': 'goblin_walk4.bmp',
        'goblin_atk1': 'goblin_atk1.bmp',
        'goblin_atk2': 'goblin_atk2.bmp',
        'goblin_atk3': 'goblin_atk3.bmp',
    }


def init(obj, params):
    obj['speed'] = SPEED
    obj['vx'] = SPEED
    obj['face'] = 1
    obj['hp'] = (params or {}).get('hp', 2)
    obj['triggers'] = []
    obj['dead'] = False


def _map_tile(map_grid, tx, ty):
    if ty < 0 or tx < 0:
        return 1
    if ty >= len(map_grid) or tx >= len(map_grid[0]):
        return 0 if ty >= len(map_grid) else 1
    return map_grid[ty][tx]


def behave(obj, keys, map_grid):
    if obj.get('dead'):
        obj['vx'] = 0
        return
    speed = abs(obj.get('speed', SPEED))
    if obj.get('hitW'):
        obj['face'] = -obj['face']
    elif obj['onG']:
        ahead_x = obj['x'] + obj['face'] * (obj['w'] / 2 + 0.1)
        if _map_tile(map_grid, int(ahead_x), int(obj['y'])) not in (1, 2):
            obj['face'] = -obj['face']
    obj['vx'] = obj['face'] * speed


def transform(obj):
    for tr in obj.get('triggers', []):
        if isinstance(tr, dict) and tr.get('name') == 'get_shot':
            obj['hp'] = obj.get('hp', 1) - 1
            obj['flash'] = 12
            if obj['hp'] <= 0:
                obj['dead'] = True
    obj['triggers'] = []
    obj['collisions'] = []
    if obj.get('dead'):
        return None
    frames, speed = ANIMS['walk']
    idx = (obj.get('t', 0) // speed) % len(frames)
    return frames[idx]


register_object_type(
    name='goblin',
    init_func=init,
    behave_func=behave,
    transform_func=transform,
    sprites_map_func=sprites_map,
    hitbox=HITBOX,
    anchor_type='ground',
    layer=LAYER_ENEMY,
    tags=['enemy', 'damage'],
    has_gravity=True,
    has_friction=False,
)
