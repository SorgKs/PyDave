#!/usr/bin/env python3
"""anims/zombie.py — патруль по земле. Не двигает x/y (это physics)."""
import math
import random

from anims import register_object_type, LAYER_ENEMY
from config import TS, VW, FPS

HITBOX = (2.5, 4.0)  # 80% спрайта walk 50×80px → 3.125×5.0 тайла
SPEED = 0.05  # 0.4 px / 16
# webdave: KILL_PADDING=49px — вынос удара вперёд на последнем кадре
ATTACK_REACH = 49.0 / TS
MELEE_GAP = 0.35  # зазор до игрока для старта атаки (тайлы)
ATTACK_SPRITE_OFFSET = -20.0 / TS  # offsetx атаки в webdave

# Видимость: ширина экрана в тайлах; P(поворот за 1с) = 50% при проверке каждый кадр
SCREEN_RANGE = VW / float(TS)
CLOSE_RANGE = SCREEN_RANGE / 3.0
TURN_CHANCE = 1.0 - 0.5 ** (1.0 / FPS)
LOS_STEP = 0.125

# Координаты в assets/sheets/dave.png (monsters/zombie.js)
ATLAS = (
    ('zombie_walk1', 0, 566, 50, 80),
    ('zombie_walk2', 50, 566, 50, 80),
    ('zombie_walk3', 100, 566, 50, 80),
    ('zombie_walk4', 150, 566, 50, 80),
    ('zombie_atk1', 200, 566, 98, 80),
    ('zombie_atk2', 298, 566, 98, 80),
    ('zombie_atk3', 396, 566, 98, 80),
    ('zombie_fall1', 988, 566, 50, 80),
    ('zombie_fall2', 1038, 566, 50, 80),
)

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
    obj['attacking'] = False
    obj['attack_t'] = 0


def _find_player(objects_list):
    """Игрок из списка объектов кадра."""
    if not objects_list:
        return None
    for other in objects_list:
        if 'player' in other.get('tags', []):
            return other
    return None


def _hitbox_rect(obj):
    """Прямоугольник хитбокса объекта в тайлах."""
    return (
        obj['x'] + obj['hitbox_offset_x'],
        obj['y'] + obj['hitbox_offset_y'],
        obj['w'],
        obj['h'],
    )


def _reset_hitbox(obj):
    """Базовый хитбокс после атаки."""
    bw, bh = HITBOX
    obj['w'] = bw
    obj['h'] = bh
    obj['hitbox_offset_x'] = -bw / 2.0
    obj['hitbox_offset_y'] = -bh


def _apply_attack_hitbox(obj, frame_idx):
    """На последнем кадре удара — хитбокс вперёд на руку."""
    bw, bh = HITBOX
    frames, _speed = ANIMS['attack']
    if frame_idx == len(frames) - 1:
        obj['w'] = bw + ATTACK_REACH
        if obj.get('face', 1) >= 0:
            obj['hitbox_offset_x'] = -bw / 2.0
        else:
            obj['hitbox_offset_x'] = -bw / 2.0 - ATTACK_REACH
    else:
        obj['w'] = bw
        obj['hitbox_offset_x'] = -bw / 2.0
    obj['h'] = bh
    obj['hitbox_offset_y'] = -bh


def _player_in_melee_range(obj, player):
    """Игрок перед зомби и достаточно близко для удара."""
    if not player or player.get('dead'):
        return False
    ax, ay, aw, ah = _hitbox_rect(obj)
    bx, by, bw, bh = _hitbox_rect(player)
    if ay + ah <= by + 0.25 or by + bh <= ay + 0.25:
        return False
    face = obj.get('face', 1)
    if face >= 0:
        if bx + bw <= ax:
            return False
        gap = bx - (ax + aw)
        return gap <= MELEE_GAP
    if ax + aw <= bx:
        return False
    gap = ax - (bx + bw)
    return gap <= MELEE_GAP


def _attack_frame_idx(obj):
    """Индекс кадра атаки по attack_t."""
    _frames, speed = ANIMS['attack']
    return obj.get('attack_t', 0) // speed


def _point_in_hitbox(x, y, other):
    hx = other['x'] + other['hitbox_offset_x']
    hy = other['y'] + other['hitbox_offset_y']
    return hx <= x <= hx + other['w'] and hy <= y <= hy + other['h']


def _line_of_sight(x0, y0, x1, y1, map_grid, obj, objects_list):
    """Прямая зомби→игрок: стена (тайл 1) или другой враг блокирует обзор."""
    dist = math.hypot(x1 - x0, y1 - y0)
    if dist < 1e-6:
        return True
    steps = max(int(dist / LOS_STEP), 1)
    for i in range(1, steps):
        t = i / float(steps)
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t
        if _map_tile(map_grid, int(x), int(y)) == 1:
            return False
        if not objects_list:
            continue
        for other in objects_list:
            if other is obj or other.get('dead'):
                continue
            if 'enemy' not in other.get('tags', []):
                continue
            if 'player' in other.get('tags', []):
                continue
            if _point_in_hitbox(x, y, other):
                return False
    return True


def _try_turn_toward_player(obj, player, map_grid, objects_list):
    """Разворот к игроку: ближе трети экрана — сразу, иначе с шансом TURN_CHANCE/кадр."""
    if not player or player.get('dead') or not obj.get('onG'):
        return
    dx = player['x'] - obj['x']
    if abs(dx) > SCREEN_RANGE:
        return
    zy = obj['y'] - obj['h'] * 0.55
    py = player['y'] - player['h'] * 0.5
    if not _line_of_sight(obj['x'], zy, player['x'], py, map_grid, obj, objects_list):
        return
    face = 1 if dx >= 0 else -1
    if obj.get('face', 1) == face:
        return
    if abs(dx) < CLOSE_RANGE:
        obj['face'] = face
        return
    if random.random() < TURN_CHANCE:
        obj['face'] = face


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


def behave(obj, keys, map_grid, objects_list=None):
    """Скорость/разворот; при приближении к Дейву — удар."""
    if obj.get('dead'):
        obj['vx'] = 0
        return

    player = _find_player(objects_list)
    attack_frames, attack_speed = ANIMS['attack']

    # Анимация удара: стоять, на последнем кадре — удлинённый хитбокс (до physics)
    if obj.get('attacking'):
        obj['vx'] = 0
        idx = _attack_frame_idx(obj)
        if idx >= len(attack_frames):
            obj['attacking'] = False
            obj['attack_t'] = 0
            obj.pop('attack_idx', None)
            _reset_hitbox(obj)
            obj['sprite_offset_x'] = 0.0
            return
        obj['attack_idx'] = idx
        _apply_attack_hitbox(obj, idx)
        obj['attack_t'] = obj.get('attack_t', 0) + 1
        return

    speed = abs(obj.get('speed', SPEED))
    if obj.get('hitW') or obj.get('hitE'):
        obj['face'] = -obj['face']
        obj['vx'] = obj['face'] * speed
        return

    # Старт удара при приближении к игроку на земле
    if obj['onG'] and _player_in_melee_range(obj, player):
        obj['attacking'] = True
        obj['attack_t'] = 0
        obj['vx'] = 0
        if player is not None:
            obj['face'] = 1 if player['x'] >= obj['x'] else -1
        _apply_attack_hitbox(obj, 0)
        return

    _try_turn_toward_player(obj, player, map_grid, objects_list)

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
            dmg = tr.get('damage', 1)
            obj['hp'] = obj.get('hp', 1) - dmg
            obj['flash'] = 12
            if obj['hp'] <= 0:
                obj['dead'] = True
    obj['triggers'] = []

    obj['collisions'] = []
    if obj.get('dead'):
        return None
    if obj.get('attacking') and obj['onG']:
        state = 'attack'
    elif not obj['onG']:
        state = 'fall'
    else:
        state = 'walk'
    obj['state'] = state
    frames, speed = ANIMS.get(state, ANIMS['walk'])
    if state == 'attack':
        idx = min(obj.get('attack_idx', 0), len(frames) - 1)
        obj['sprite_offset_x'] = ATTACK_SPRITE_OFFSET
    else:
        obj['sprite_offset_x'] = 0.0
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
