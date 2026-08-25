#!/usr/bin/env python3
"""
anims/dave.py — Дэйв: игрок
НОВАЯ АРХИТЕКТУРА: функции вместо класса
"""
from anims import register_object_type
import pygame

# Константы
HITBOX = (36, 48)
ANCHOR_TYPE = 'ground'
LAYER = 1  # LAYER_PLAYER

ATLAS = [
    ('dave_idle', 0, 0, 48, 64),
    ('dave_walk1', 48, 0, 48, 64),
    ('dave_walk2', 96, 0, 48, 64),
    ('dave_walk3', 144, 0, 48, 64),
    ('dave_walk4', 192, 0, 48, 64),
    ('dave_jump', 240, 0, 48, 64),
    ('dave_fall', 336, 0, 48, 64),
    ('dave_shoot', 864, 0, 58, 64),
    ('dave_shoot2', 922, 0, 58, 64),
    ('dave_aimup', 980, 0, 42, 64),
    ('dave_aimdown', 1064, 0, 48, 64),
]

ANIMS = {
    'idle':    ((['dave_idle'],), 1),
    'walk':    ((['dave_walk1', 'dave_walk2', 'dave_walk3', 'dave_walk4'],
                 ['dave_walk1', 'dave_walk2']), 10),
    'jump':    ((['dave_jump'],), 1),
    'fall':    ((['dave_fall'], ['dave_jump']), 1),
    'shoot':   ((['dave_shoot', 'dave_shoot2'], ['dave_shoot']), 6),
    'aimup':   ((['dave_aimup'],), 1),
    'aimdown': ((['dave_aimdown'],), 1),
}


def init(obj, params):
    """Инициализация объекта Дэйв."""
    obj['cool'] = 0
    obj['inv'] = 0
    obj['drop'] = 0
    obj['wasG'] = False
    obj['aim_up'] = False
    obj['aim_down'] = False
    return ['dave_idle', 'dave_walk1', 'dave_walk2', 'dave_walk3', 'dave_walk4', 
            'dave_jump', 'dave_fall', 'dave_shoot', 'dave_shoot2', 'dave_aimup', 'dave_aimdown']


def behave(obj, input_data, ctx):
    """Логика управления Дэйвом."""
    if ctx is None:
        return
    
    pressed = input_data.get('pressed', []) if input_data else []
    held = input_data.get('held', {}) if input_data else {}
    
    # --- УПРАВЛЕНИЕ ---
    left = held.get(pygame.K_LEFT, False) or held.get(pygame.K_a, False)
    right = held.get(pygame.K_RIGHT, False) or held.get(pygame.K_d, False)
    jump = pygame.K_SPACE in pressed
    obj['aim_up'] = held.get(pygame.K_UP, False) or held.get(pygame.K_w, False)
    obj['aim_down'] = held.get(pygame.K_DOWN, False) or held.get(pygame.K_s, False)
    drop = obj['aim_down'] and jump
    
    # --- ДВИЖЕНИЕ ---
    acc = .5 if obj['onG'] else .3
    vmax = 2.3
    if left:
        obj['vx'] = max(obj['vx'] - acc, -vmax)
        obj['face'] = -1
    elif right:
        obj['vx'] = min(obj['vx'] + acc, vmax)
        obj['face'] = 1
    else:
        f = .4 if obj['onG'] else .1
        if obj['vx'] > 0:
            obj['vx'] = max(0, obj['vx'] - f)
        elif obj['vx'] < 0:
            obj['vx'] = min(0, obj['vx'] + f)
    
    # --- ТАЙМЕРЫ ---
    if obj.get('drop', 0) > 0:
        obj['drop'] -= 1
    if obj.get('inv', 0) > 0:
        obj['inv'] -= 1
    if obj.get('cool', 0) > 0:
        obj['cool'] -= 1
    
    # --- ПРЫЖОК ---
    if jump and obj['onG'] and obj.get('drop', 0) <= 0:
        obj['vy'] = -6.5
        if hasattr(ctx, 'play'):
            ctx.play('jump')
        if hasattr(ctx, 'add_parts'):
            ctx.add_parts(obj['x'] + 6, obj['y'] + 28, 5, '#8a7f9a', 1, .05)
    
    # --- СПРЫГИВАНИЕ ---
    if drop and obj['onG'] and obj.get('drop', 0) <= 0:
        ty = int((obj['y'] + obj['h'] + 1) // ctx.TS)
        on_plat = False
        for tx in range(int(obj['x'] // ctx.TS), int((obj['x'] + obj['w']) // ctx.TS) + 1):
            if 0 <= ty < ctx.ROWS and ctx.grid[ty][tx] == 2 and ctx.tile_at(tx, ty) != 1:
                on_plat = True
                break
        if on_plat:
            obj['drop'] = 12
            obj['onG'] = False
            obj['vy'] = 1.0
    
    # --- ЗВУК ПРИЗЕМЛЕНИЯ ---
    if obj['onG'] and not obj.get('wasG', False):
        if hasattr(ctx, 'play'):
            ctx.play('land')
    obj['wasG'] = obj['onG']
    
    # --- ВЫСТРЕЛ ---
    shoot_keys = [pygame.K_x, pygame.K_j, pygame.K_k]
    if any(held.get(k, False) for k in shoot_keys) and obj.get('cool', 0) <= 0:
        obj['cool'] = 18
        if hasattr(ctx, 'play'):
            ctx.play('shoot')
        if hasattr(ctx, 'shake'):
            ctx.shake(1.2)
        obj['vx'] -= obj['face'] * 1.8


def transform(obj):
    """Обработка коллизий для Дэйва."""
    for col in obj.get('collisions', []):
        target = col.get('target')
        normal = col.get('normal', (0, 0))
        depth = col.get('depth', 0)
        
        # Обработка коллизий с врагами (урон)
        if target and hasattr(target, 'tags') and 'damage' in target.get('tags', []):
            if obj.get('inv', 0) <= 0:
                obj['inv'] = 30
                obj['vy'] = -5
                if hasattr(obj, '_ctx') and hasattr(obj._ctx, 'hurt'):
                    obj._ctx.hurt(target.x)
        
        # Обработка подбора предметов
        if target and hasattr(target, 'tags') and 'collectible' in target.get('tags', []):
            pass
    
    obj['collisions'] = []


def get_sprite(obj):
    """Возвращает имя текущего спрайта."""
    state = 'idle'
    
    if obj.get('aim_up', False):
        state = 'aimup'
    elif obj.get('aim_down', False):
        state = 'aimdown'
    elif obj.get('cool', 0) > 4:
        state = 'shoot'
    elif not obj['onG']:
        state = 'fall' if obj['vy'] > 0 else 'jump'
    elif abs(obj['vx']) > .3:
        state = 'walk'
    
    if state not in ANIMS:
        state = 'idle'
    
    anim_data = ANIMS[state]
    sequences = anim_data[0]
    speed = anim_data[1] if len(anim_data) > 1 else 1
    
    seq = sequences[0]
    frame_idx = (obj.get('t', 0) // speed) % len(seq)
    return seq[frame_idx]


# Регистрируем тип объекта
register_object_type(
    name='dave',
    init_func=init,
    behave_func=behave,
    transform_func=transform,
    get_sprite_func=get_sprite,
    hitbox=HITBOX,
    anchor_type=ANCHOR_TYPE,
    layer=LAYER,
    tags=['player'],
)
