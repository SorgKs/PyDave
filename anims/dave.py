#!/usr/bin/env python3
"""anims/dave.py — игрок. Координаты/скорости в тайлах."""
from anims import register_object_type, LAYER_PLAYER
from config import VW, TS, FPS
from weapons import get_weapon
import math
import sys

# Хитбокс в тайлах (бывш. 36×48 px при TS=16)
HITBOX = (2.25, 3.0)
ANCHOR_TYPE = 'ground'

# Скорости в тайлах/кадр
ACC_GROUND = 0.03125
ACC_AIR = 0.01875
VMAX = 0.14375
JUMP_VY = -0.518  # ~15% ниже прежнего -0.609375
SHOOT_RECOIL = 0.1125
SHOOT_STOP_FRAMES = FPS * 2 // 5   # 0.4 с — без управления после выстрела
SHOOT_COOL_FRAMES = FPS // 2       # 0.5 с — до следующего выстрела
SHOOT_BUFFER_FRAMES = int(FPS * 0.2)  # запоминание нажатия выстрела
IDLETIMEOUT_FRAMES = int(FPS * 0.4)  # простой перед автоперезарядкой
RELOAD_ANIM_SPEED = max(1, round(FPS / 3.6))  # webdave animSpeed=3.6
RELOAD_SPRITE = ('reload_0', 'reload_1')
FRICTION_OWN_G = 0.025
FRICTION_OWN_A = 0.00625

# Выстрел — всё в тайлах (1 экран по ширине вьюпорта)
SHOT_RANGE = VW / float(TS)
SHOT_STEP = 0.125
SPRITE_H = 4.0  # высота спрайта Дейва в тайлах
AIM_FAN_RAYS = 7
AIM_FAN_CENTER_DEG = 45
AIM_FAN_SPREAD_DEG = 3

# Координаты в assets/sheets/dave.png (webdave player.js)
ATLAS = (
    ('dave_reload1', 768, 0, 48, 64),
    ('dave_reload2', 816, 0, 48, 64),
)

# Game.js — playerDeathZombie (5×96×96) и playerDeathKnife (4×96×96), y=66
DEATH_ZOMBIE_FRAMES = (
    'dave_death_zombie1', 'dave_death_zombie2', 'dave_death_zombie3',
    'dave_death_zombie4', 'dave_death_zombie5',
)
DEATH_ZOMBIE_SPEED = max(1, FPS // 4)   # animSpeed=4 в webdave
DEATH_ZOMBIE_HOLD = max(1, int(FPS * 0.3))
DEATH_ZOMBIE_SIZE = (96, 96)  # px

DEATH_ATLAS = tuple(
    ('dave_death_zombie%d' % (i + 1), i * 96, 66, 96, 96) for i in range(5)
) + tuple(
    ('dave_death_knife%d' % (i + 1), 480 + i * 96, 66, 96, 96) for i in range(4)
)

# deaths-of-dave.png — 40 сцен 48×48 → death_00 … death_39 (split_dave_death.py)
DEATH_GALLERY_COUNT = 40

ANIMS = {
    'idle': (['dave_idle'], 1),
    'walk': (['dave_walk1', 'dave_walk2', 'dave_walk3', 'dave_walk4'], 10),
    'jump': (['dave_jump'], 1),
    'fall': (['dave_fall'], 1),
    'shoot': (['shoot_straight_0', 'shoot_straight_1'], 3),
    'shoot_up': (['shoot_up_0', 'shoot_up_1'], 3),
    'shoot_down': (['shoot_down_0', 'shoot_down_1'], 3),
    'reload': (list(RELOAD_SPRITE), RELOAD_ANIM_SPEED),
    'aimup': (['aim_up'], 1),
    'aimdown': (['aim_down'], 1),
    'aimstraight': (['aim_straight'], 1),
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
        'shoot_straight_0': 'shoot_straight_0.bmp',
        'shoot_straight_1': 'shoot_straight_1.bmp',
        'shoot_up_0': 'shoot_up_0.bmp',
        'shoot_up_1': 'shoot_up_1.bmp',
        'shoot_down_0': 'shoot_down_0.bmp',
        'shoot_down_1': 'shoot_down_1.bmp',
        'reload_0': 'reload_0.bmp',
        'reload_1': 'reload_1.bmp',
        'aim_up': 'aim_up.bmp',
        'aim_down': 'aim_down.bmp',
        'aim_straight': 'aim_straight.bmp',
    }


def _weapon(obj):
    """Текущее оружие игрока."""
    return get_weapon(obj.get('weapon', 'double_barrel'))


def _can_auto_reload(obj, left, right, aiming):
    """Условия автоперезарядки на земле."""
    return (obj['onG'] and not left and not right and not aiming
            and obj.get('shoot_stop', 0) <= 0
            and not obj.get('pending_shoot')
            and obj.get('ammo', 0) < obj.get('max_ammo', 0))


def _reload_needed(obj):
    """Сколько патронов не хватает до полного магазина."""
    return max(0, obj.get('max_ammo', 0) - obj.get('ammo', 0))


def _reload_sequence_len(needed):
    """Длина анимации: 1 патрон → 1-2-1 (3), 2 патрона → 1-2-1-2-1 (5)."""
    if needed <= 0:
        return 0
    return 2 * needed + 1


def _start_reload(obj):
    """Запуск перезарядки с длиной под текущий недостаток патронов."""
    needed = _reload_needed(obj)
    obj['reloading'] = True
    obj['reload_t'] = 0
    obj['reload_len'] = _reload_sequence_len(needed)
    obj['reload_shells_added'] = 0


def _tick_reload(obj, left, right, aiming):
    """
    Анимация 1-2-1… без пауз: для N патронов — 1-2-1-2-…-1 (2N+1 кадров).
    +1 патрон на каждом финальном «1» (шаги 2, 4, 6…).
    """
    if not obj.get('reloading'):
        return
    if not _can_auto_reload(obj, left, right, aiming):
        obj['reloading'] = False
        obj['reload_t'] = 0
        return

    step = obj.get('reload_t', 0) // RELOAD_ANIM_SPEED
    if step >= obj.get('reload_len', 0):
        obj['reloading'] = False
        obj['reload_t'] = 0
        return

    tick = obj.get('reload_t', 0) % RELOAD_ANIM_SPEED

    # +1 на кадрах 1-2-[1], 1-2-1-2-[1], …
    if tick == 0 and step >= 2 and step % 2 == 0:
        shells = step // 2
        if obj.get('reload_shells_added', 0) < shells:
            if obj.get('ammo', 0) < obj.get('max_ammo', 0):
                obj['ammo'] += 1
                obj['pending_reload_sfx'] = True
            obj['reload_shells_added'] = shells

    obj['reload_t'] = obj.get('reload_t', 0) + 1

    if obj.get('ammo', 0) >= obj.get('max_ammo', 0):
        obj['reloading'] = False
        obj['reload_t'] = 0


def _start_shoot(obj, aim_up, aim_down):
    """Старт анимации выстрела; при пустом магазине — холостой (dry)."""
    w = _weapon(obj)
    obj['cool'] = w['shoot_cool']
    obj['shoot_stop'] = w['shoot_stop']
    obj['pending_shoot'] = True
    obj['shoot_aim_up'] = aim_up
    obj['shoot_aim_down'] = aim_down
    obj['shoot_dry'] = obj.get('ammo', 0) <= 0
    obj['shoot_buffer'] = 0
    obj['idle_time'] = 0


def _can_start_shoot(obj):
    """Можно начать новый выстрел — только стоя на поверхности."""
    return (obj['onG']
            and not obj.get('reloading')
            and obj.get('cool', 0) <= 0
            and obj.get('shoot_stop', 0) <= 0)


def init(obj, params):
    """Индивидуальные поля игрока."""
    obj['weapon'] = 'double_barrel'
    w = _weapon(obj)
    obj['ammo'] = w['max_ammo']
    obj['max_ammo'] = w['max_ammo']
    obj['cool'] = 0
    obj['shoot_stop'] = 0
    obj['reloading'] = False
    obj['reload_t'] = 0
    obj['reload_len'] = 0
    obj['reload_shells_added'] = 0
    obj['idle_time'] = 0
    obj['inv'] = 0
    obj['drop'] = 0
    obj['wasG'] = False
    obj['aim_up'] = False
    obj['aim_down'] = False
    obj['dead'] = False
    obj['pending_jump_sfx'] = False
    obj['pending_land_sfx'] = False
    obj['pending_shoot'] = False
    obj['shoot_dry'] = False
    obj['shoot_buffer'] = 0
    obj['shoot_buffer_aim_up'] = False
    obj['shoot_buffer_aim_down'] = False
    obj['pending_reload_sfx'] = False
    obj['pending_no_ammo_sfx'] = False
    obj['shoot_aim_up'] = False
    obj['shoot_aim_down'] = False
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


def _muzzle_pos(obj):
    """Точка вылета луча (тайлы)."""
    face = 1 if obj.get('face', 1) >= 0 else -1
    x0 = obj['x'] + face * (obj['w'] * 0.5 + 0.05)
    y0 = obj['y'] - SPRITE_H * 0.75
    return face, x0, y0


def _cast_ray(x0, y0, dx, dy, map_grid, objects_list, shooter):
    """Первое пересечение луча со стеной или врагом."""
    dist = 0.0
    while dist <= SHOT_RANGE:
        x = x0 + dx * dist
        y = y0 + dy * dist
        if _map_tile(map_grid, int(x), int(y)) == 1:
            return {'dist': dist, 'x': x, 'y': y, 'kind': 'wall', 'obj': None}
        for other in objects_list:
            if other is shooter or other.get('dead'):
                continue
            if 'enemy' not in other.get('tags', []):
                continue
            if _point_in_hitbox(x, y, other):
                return {'dist': dist, 'x': x, 'y': y, 'kind': 'enemy', 'obj': other}
        dist += SHOT_STEP
    return None


def _pick_shot_hit(hits):
    """
    Выбор точки попадания из списка пересечений лучей.
    Приоритет: ближайший враг; при нескольких лучах — точка ближе к центру врага;
    иначе ближайшая стена.
    """
    enemy_hits = [h for h in hits if h['kind'] == 'enemy']
    if enemy_hits:
        by_enemy = {}
        for h in enemy_hits:
            by_enemy.setdefault(id(h['obj']), []).append(h)
        best_id = min(
            by_enemy.keys(),
            key=lambda eid: min(h['dist'] for h in by_enemy[eid]))
        group = by_enemy[best_id]
        if len(group) > 1:
            enemy = group[0]['obj']
            cx = enemy['x'] + enemy['hitbox_offset_x'] + enemy['w'] * 0.5
            cy = enemy['y'] + enemy['hitbox_offset_y'] + enemy['h'] * 0.5
            return min(group, key=lambda h: (h['x'] - cx) ** 2 + (h['y'] - cy) ** 2)
        return group[0]
    wall_hits = [h for h in hits if h['kind'] == 'wall']
    if wall_hits:
        return min(wall_hits, key=lambda h: h['dist'])
    return None


def _set_shot_fx(obj, x0, y0, hit, face):
    """Записывает pending_shot_fx и триггер get_shot для выбранного врага."""
    damage = _weapon(obj)['damage']
    if hit is None:
        obj['pending_shot_fx'] = {
            'x0': x0, 'y0': y0,
            'x': x0, 'y': y0,
            'face': face,
            'kind': 'miss',
            'colors': _DEFAULT_SHOT_COLORS,
        }
        return
    hit_obj = hit.get('obj')
    if hit['kind'] == 'enemy' and hit_obj:
        hit_obj.setdefault('triggers', []).append({
            'name': 'get_shot',
            'damage': damage,
        })
    dx = x0 - hit['x']
    dy = y0 - hit['y']
    ln = math.hypot(dx, dy) or 1.0
    obj['pending_shot_fx'] = {
        'x0': x0, 'y0': y0,
        'x': hit['x'], 'y': hit['y'],
        'face': face,
        'kind': hit['kind'],
        'colors': _shot_colors(hit_obj),
        'dir_x': dx / ln,
        'dir_y': dy / ln,
    }


def _shot_aim_fan(obj, map_grid, objects_list, downward=False):
    """
    Hitscan веером: 7 лучей, центральный 45°, шаг 3°.
    downward=True — вниз, иначе вверх.
    """
    face, x0, y0 = _muzzle_pos(obj)
    mid = (AIM_FAN_RAYS - 1) // 2
    hits = []
    for i in range(AIM_FAN_RAYS):
        deg = AIM_FAN_CENTER_DEG + (i - mid) * AIM_FAN_SPREAD_DEG
        rad = math.radians(deg)
        dx = face * math.cos(rad)
        dy = math.sin(rad) if downward else -math.sin(rad)
        h = _cast_ray(x0, y0, dx, dy, map_grid, objects_list, obj)
        if h:
            hits.append(h)
    _set_shot_fx(obj, x0, y0, _pick_shot_hit(hits), face)


def shot_aim_up(obj, map_grid, objects_list):
    _shot_aim_fan(obj, map_grid, objects_list, downward=False)


def shot_aim_down(obj, map_grid, objects_list):
    _shot_aim_fan(obj, map_grid, objects_list, downward=True)


def shot(obj, map_grid, objects_list):
    """
    Hitscan: горизонтально или веер при shoot_aim_up / shoot_aim_down.
    Стена или враг — попадание; врагу пишется триггер get_shot.
    Результат для частиц: obj['pending_shot_fx'].
    """
    if obj.get('shoot_aim_up'):
        shot_aim_up(obj, map_grid, objects_list)
        return
    if obj.get('shoot_aim_down'):
        shot_aim_down(obj, map_grid, objects_list)
        return
    face, x0, y0 = _muzzle_pos(obj)
    hit = _cast_ray(x0, y0, float(face), 0.0, map_grid, objects_list, obj)
    _set_shot_fx(obj, x0, y0, hit, face)


def fire_shot_if_ready(obj, map_grid, objects_list):
    """
    Выстрел на 2-м кадре анимации (elapsed >= speed).
    Возвращает pending_shot_fx или None.
    """
    if not obj.get('pending_shoot'):
        return None
    w = _weapon(obj)
    speed = w['shoot_anim_speed']
    elapsed = w['shoot_stop'] - obj.get('shoot_stop', 0)
    if elapsed < speed:
        return None
    obj['pending_shoot'] = False
    obj['shoot_aim_up'] = False
    obj['shoot_aim_down'] = False
    if obj.get('shoot_dry'):
        obj['shoot_dry'] = False
        obj['pending_no_ammo_sfx'] = True
        return None
    obj['ammo'] = max(0, obj.get('ammo', 0) - 1)
    obj['vx'] -= obj['face'] * w['recoil']
    shot(obj, map_grid, objects_list)
    fx = obj.get('pending_shot_fx')
    return fx


def behave(obj, keys, map_grid, objects_list=None):
    """behave(obj, keys, map): только vel/face/флаги, не x/y."""
    keys = keys or set()

    left = 'l=' in keys or 'l+' in keys
    right = 'r=' in keys or 'r+' in keys
    jump = 'j+' in keys
    # Прицел вверх/вниз — только стоя на поверхности
    obj['aim_up'] = obj['onG'] and ('u=' in keys or 'u+' in keys)
    obj['aim_down'] = obj['onG'] and ('d=' in keys or 'd+' in keys)
    drop = obj['aim_down'] and jump
    aiming = obj['aim_up'] or obj['aim_down']
    stopped = obj.get('shoot_stop', 0) > 0 or obj.get('reloading')

    acc = ACC_GROUND if obj['onG'] else ACC_AIR
    if aiming or stopped:
        # Прицел или пауза после выстрела — без ввода, скорость затухает
        f = FRICTION_OWN_G if obj['onG'] else FRICTION_OWN_A
        if obj['vx'] > 0:
            obj['vx'] = max(0.0, obj['vx'] - f)
        elif obj['vx'] < 0:
            obj['vx'] = min(0.0, obj['vx'] + f)
    elif left:
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
    if obj.get('shoot_stop', 0) > 0:
        obj['shoot_stop'] -= 1

    if jump and obj['onG'] and obj.get('drop', 0) <= 0 and not drop and not stopped:
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

    # Автоперезарядка при простое на земле
    if (_can_auto_reload(obj, left, right, aiming)
            and not obj.get('reloading')):
        obj['idle_time'] = obj.get('idle_time', 0) + 1
    elif not obj.get('reloading'):
        obj['idle_time'] = 0

    if (not obj.get('reloading')
            and _can_auto_reload(obj, left, right, aiming)
            and obj.get('idle_time', 0) >= IDLETIMEOUT_FRAMES):
        _start_reload(obj)
        obj['idle_time'] = 0

    _tick_reload(obj, left, right, aiming)

    shoot_pressed = 's+' in keys
    if shoot_pressed and obj['onG'] and not obj.get('reloading'):
        obj['shoot_buffer'] = SHOOT_BUFFER_FRAMES
        obj['shoot_buffer_aim_up'] = obj['aim_up']
        obj['shoot_buffer_aim_down'] = obj['aim_down']

    fired = False
    if _can_start_shoot(obj) and (shoot_pressed or obj.get('shoot_buffer', 0) > 0):
        _start_shoot(
            obj,
            obj.get('shoot_buffer_aim_up', obj['aim_up']),
            obj.get('shoot_buffer_aim_down', obj['aim_down']),
        )
        fired = True

    if not fired and obj.get('shoot_buffer', 0) > 0:
        obj['shoot_buffer'] -= 1


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
            obj['death_killer'] = target
        if 'collectible' in tags:
            target['taken'] = True

    obj['collisions'] = []

    if obj.get('reloading'):
        state = 'reload'
    elif obj.get('shoot_stop', 0) > 0:
        if obj.get('shoot_aim_up'):
            state = 'shoot_up'
        elif obj.get('shoot_aim_down'):
            state = 'shoot_down'
        else:
            state = 'shoot'
    elif obj.get('aim_up'):
        state = 'aimup'
    elif obj.get('aim_down'):
        state = 'aimdown'
    elif not obj['onG']:
        state = 'jump'
    elif abs(obj['vx']) > 0.02:
        state = 'walk'
    else:
        state = 'idle'

    obj['state'] = state
    frames, speed = ANIMS.get(state, ANIMS['idle'])
    if state in ('shoot', 'shoot_up', 'shoot_down'):
        w = _weapon(obj)
        elapsed = w['shoot_stop'] - obj.get('shoot_stop', 0)
        idx = min(elapsed // w['shoot_anim_speed'], len(frames) - 1)
    elif state == 'reload':
        # webdave: offsetx=-7 px для кадра перезарядки
        obj['sprite_offset_x'] = -7.0 / TS
        step = (obj.get('reload_t', 0) // RELOAD_ANIM_SPEED)
        idx = 0 if step % 2 == 0 else 1
    else:
        obj['sprite_offset_x'] = 0.0
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
