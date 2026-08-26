#!/usr/bin/env python3
"""anims/dave.py — игрок. Координаты/скорости в тайлах."""
from anims import register_object_type, LAYER_PLAYER
from config import VW, TS
import sys

# Хитбокс в тайлах (бывш. 36×48 px при TS=16)
HITBOX = (2.25, 3.0)
ANCHOR_TYPE = 'ground'

# Скорости в тайлах/кадр
ACC_GROUND = 0.03125
ACC_AIR = 0.01875
VMAX = 0.14375
JUMP_VY = -0.40625
SHOOT_RECOIL = 0.1125
FRICTION_OWN_G = 0.025
FRICTION_OWN_A = 0.00625

# Выстрел — всё в тайлах (1 экран по ширине вьюпорта)
SHOT_RANGE = VW / float(TS)
SHOT_STEP = 0.125
SPRITE_H = 4.0  # высота спрайта Дейва в тайлах

ANIMS = {
    'idle': (['dave_idle'], 1),
    'walk': (['dave_walk1', 'dave_walk2', 'dave_walk3', 'dave_walk4'], 10),
    'jump': (['dave_jump'], 1),
    'fall': (['dave_fall'], 1),
    'shoot': (['dave_shoot', 'dave_shoot2'], 6),
    'aimup': (['dave_aimup'], 1),
    'aimdown': (['dave_aimdown'], 1),
}


def sprites_map():
    return {
        'dave_idle': 'dave_idle.bmp',
        'dave_walk1': 'dave_walk1.bmp',
        'dave_walk2': 'dave_walk2.bmp',
        'dave_walk3': 'dave_walk3.bmp',
        'dave_walk4': 'dave_walk4.bmp',
        'dave_jump': 'dave_jump.bmp',
        'dave_fall': 'dave_fall.bmp',
        'dave_shoot': 'dave_shoot.bmp',
        'dave_shoot2': 'dave_shoot2.bmp',
        'dave_aimup': 'dave_aimup.bmp',
        'dave_aimdown': 'dave_aimdown.bmp',
    }


def init(obj, params):
    """Индивидуальные поля игрока."""
    obj['cool'] = 0
    obj['inv'] = 0
    obj['drop'] = 0
    obj['wasG'] = False
    obj['aim_up'] = False
    obj['aim_down'] = False
    obj['dead'] = False
    obj['pending_jump_sfx'] = False
    obj['pending_land_sfx'] = False
    obj['pending_shoot'] = False
    obj['pending_shot_fx'] = None
    obj['has_friction'] = False


def _map_tile(map_grid, tx, ty):
    if ty < 0 or tx < 0:
        return 1
    if ty >= len(map_grid) or tx >= len(map_grid[0]):
        return 0
    return map_grid[ty][tx]


def _point_in_hitbox(x, y, other):
    hx = other['x'] + other['hitbox_offset_x']
    hy = other['y'] + other['hitbox_offset_y']
    return hx <= x <= hx + other['w'] and hy <= y <= hy + other['h']


# Дефолт частиц попадания (если у типа нет get_shot)
_DEFAULT_SHOT_COLORS = ('#000000', '#ffffff')


def _shot_colors(hit_obj):
    """Если у модуля типа есть get_shot() — его цвета, иначе чёрный/белый."""
    if not hit_obj:
        return _DEFAULT_SHOT_COLORS
    type_mod = sys.modules.get('anims.' + hit_obj.get('type', ''))
    fn = getattr(type_mod, 'get_shot', None) if type_mod else None
    if callable(fn):
        return fn()
    return _DEFAULT_SHOT_COLORS


def shot(obj, map_grid, objects_list):
    """
    Hitscan сразу: луч вперёд на 1 экран.
    Стена или враг — попадание; врагу пишется триггер get_shot.
    Результат для частиц: obj['pending_shot_fx'].
    """
    face = 1 if obj.get('face', 1) >= 0 else -1
    # дуло: перед хитбоксом, на 3/4 высоты спрайта от ног (тайлы)
    x0 = obj['x'] + face * (obj['w'] * 0.5 + 0.05)
    y0 = obj['y'] - SPRITE_H * 0.75

    hit_x, hit_y = x0, y0
    hit_kind = 'miss'
    hit_obj = None
    dist = 0.0

    while dist <= SHOT_RANGE:
        x = x0 + face * dist
        y = y0
        hit_x, hit_y = x, y

        if _map_tile(map_grid, int(x), int(y)) == 1:
            hit_kind = 'wall'
            break

        for other in objects_list:
            if other is obj or other.get('dead'):
                continue
            if 'enemy' not in other.get('tags', []):
                continue
            if _point_in_hitbox(x, y, other):
                other.setdefault('triggers', []).append({'name': 'get_shot'})
                hit_kind = 'enemy'
                hit_obj = other
                break
        if hit_kind == 'enemy':
            break

        dist += SHOT_STEP

    obj['pending_shot_fx'] = {
        'x0': x0, 'y0': y0,
        'x': hit_x, 'y': hit_y,
        'face': face,
        'kind': hit_kind,
        'colors': _shot_colors(hit_obj),
    }


def behave(obj, keys, map_grid):
    """behave(obj, keys, map): только vel/face/флаги, не x/y."""
    keys = keys or set()

    left = 'l=' in keys or 'l+' in keys
    right = 'r=' in keys or 'r+' in keys
    jump = 'j+' in keys
    obj['aim_up'] = 'u=' in keys or 'u+' in keys
    obj['aim_down'] = 'd=' in keys or 'd+' in keys
    drop = obj['aim_down'] and jump

    acc = ACC_GROUND if obj['onG'] else ACC_AIR
    if left:
        obj['vx'] = max(obj['vx'] - acc, -VMAX)
        obj['face'] = -1
    elif right:
        obj['vx'] = min(obj['vx'] + acc, VMAX)
        obj['face'] = 1
    else:
        f = FRICTION_OWN_G if obj['onG'] else FRICTION_OWN_A
        if obj['vx'] > 0:
            obj['vx'] = max(0.0, obj['vx'] - f)
        elif obj['vx'] < 0:
            obj['vx'] = min(0.0, obj['vx'] + f)

    if obj.get('drop', 0) > 0:
        obj['drop'] -= 1
    if obj.get('inv', 0) > 0:
        obj['inv'] -= 1
    if obj.get('cool', 0) > 0:
        obj['cool'] -= 1

    if jump and obj['onG'] and obj.get('drop', 0) <= 0 and not drop:
        obj['vy'] = JUMP_VY
        obj['pending_jump_sfx'] = True

    if drop and obj['onG'] and obj.get('drop', 0) <= 0:
        foot_ty = int(obj['y'])
        hx = obj['x'] + obj['hitbox_offset_x']
        on_plat = False
        for tx in range(int(hx), int(hx + obj['w'] - 1e-6) + 1):
            if _map_tile(map_grid, tx, foot_ty) == 2:
                on_plat = True
                break
        if on_plat:
            obj['drop'] = 12
            obj['onG'] = False
            obj['vy'] = 0.06

    if obj['onG'] and not obj.get('wasG', False):
        obj['pending_land_sfx'] = True
    obj['wasG'] = obj['onG']

    if ('s=' in keys or 's+' in keys) and obj.get('cool', 0) <= 0:
        obj['cool'] = 18
        obj['pending_shoot'] = True
        obj['vx'] -= obj['face'] * SHOOT_RECOIL


def transform(obj):
    """Реакция на коллизии + ключ спрайта. Не меняет vx/vy."""
    for col in obj.get('collisions', []):
        if col.get('kind') != 'object':
            continue
        target = col.get('target')
        if not target:
            continue
        tags = target.get('tags', [])
        if 'damage' in tags and obj.get('inv', 0) <= 0:
            obj['inv'] = 85
            obj['dead'] = True
        if 'collectible' in tags:
            target['taken'] = True

    obj['collisions'] = []

    if obj.get('aim_up'):
        state = 'aimup'
    elif obj.get('aim_down'):
        state = 'aimdown'
    elif obj.get('cool', 0) > 4:
        state = 'shoot'
    elif not obj['onG']:
        state = 'fall' if obj['vy'] > 0 else 'jump'
    elif abs(obj['vx']) > 0.02:
        state = 'walk'
    else:
        state = 'idle'

    obj['state'] = state
    frames, speed = ANIMS.get(state, ANIMS['idle'])
    idx = (obj.get('t', 0) // speed) % len(frames)
    return frames[idx]


register_object_type(
    name='dave',
    init_func=init,
    behave_func=behave,
    transform_func=transform,
    sprites_map_func=sprites_map,
    hitbox=HITBOX,
    anchor_type=ANCHOR_TYPE,
    layer=LAYER_PLAYER,
    tags=['player'],
    has_gravity=True,
    has_friction=False,
)
