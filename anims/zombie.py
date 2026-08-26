#!/usr/bin/env python3
"""anims/zombie.py — патруль по земле. Не двигает x/y (это physics)."""
from anims import register_object_type, LAYER_ENEMY

HITBOX = (2.5, 4.0)  # 80% спрайта walk 50×80px → 3.125×5.0 тайла
SPEED = 0.05  # 0.4 px / 16

ANIMS = {
    'walk': (['zombie_walk1', 'zombie_walk2', 'zombie_walk3', 'zombie_walk4'], 20),
    'attack': (['zombie_atk1', 'zombie_atk2', 'zombie_atk3'], 22),
    'fall': (['zombie_fall1', 'zombie_fall2'], 16),
}


def sprites_map():
    return {
        'zombie_walk1': 'zombie_walk1.bmp',
        'zombie_walk2': 'zombie_walk2.bmp',
        'zombie_walk3': 'zombie_walk3.bmp',
        'zombie_walk4': 'zombie_walk4.bmp',
        'zombie_atk1': 'zombie_atk1.bmp',
        'zombie_atk2': 'zombie_atk2.bmp',
        'zombie_atk3': 'zombie_atk3.bmp',
        'zombie_fall1': 'zombie_fall1.bmp',
        'zombie_fall2': 'zombie_fall2.bmp',
    }


def get_shot():
    """Цвета частиц при попадании: красный и чёрный."""
    return ('#e23b4e', '#000000')


def init(obj, params):
    obj['speed'] = SPEED
    if params and 'vx' in params:
        obj['vx'] = float(params['vx'])
    else:
        obj['vx'] = SPEED
    obj['face'] = 1 if obj['vx'] >= 0 else -1
    if params and 'hp' in params:
        obj['hp'] = params['hp']
    else:
        obj['hp'] = 2
    obj['triggers'] = []
    obj['dead'] = False


def _map_tile(map_grid, tx, ty):
    if ty < 0 or tx < 0:
        return 1
    rows = len(map_grid)
    if ty >= rows:
        return 0
    cols = len(map_grid[0]) if rows else 0
    if tx >= cols:
        return 1
    return map_grid[ty][tx]


def behave(obj, keys, map_grid):
    """Только намерение скорости; разворот у края/стены."""
    if obj.get('dead'):
        obj['vx'] = 0
        return
    speed = abs(obj.get('speed', SPEED))
    if obj.get('hitW'):
        obj['face'] = -obj['face']
        obj['vx'] = obj['face'] * speed
        return

    if obj['onG']:
        # Точка впереди у ног
        ahead_x = obj['x'] + obj['face'] * (obj['w'] / 2 + 0.1)
        gx = int(ahead_x)
        gy = int(obj['y'])
        ground = _map_tile(map_grid, gx, gy) in (1, 2)
        if not ground:
            obj['face'] = -obj['face']

    obj['vx'] = obj['face'] * speed


def transform(obj):
    # Триггер get_shot: −1 HP, при 0 — смерть
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
    if not obj['onG']:
        state = 'fall'
    else:
        state = 'walk'
    obj['state'] = state
    frames, speed = ANIMS.get(state, ANIMS['walk'])
    idx = (obj.get('t', 0) // speed) % len(frames)
    return frames[idx]


register_object_type(
    name='zombie',
    init_func=init,
    behave_func=behave,
    transform_func=transform,
    sprites_map_func=sprites_map,
    hitbox=HITBOX,
    anchor_type='ground',
    layer=LAYER_ENEMY,
    tags=['solid', 'damage', 'enemy'],
    has_gravity=True,
    has_friction=False,
)
