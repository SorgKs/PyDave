#!/usr/bin/env python3
"""
anims/zombie.py — Зомби: патруль по земле
НОВАЯ АРХИТЕКТУРА: функции вместо класса
"""
from anims import register_object_type
import pygame

HITBOX = (16, 36)
ANCHOR_TYPE = 'ground'
LAYER = 2  # LAYER_ENEMY

ATLAS = [
    ('zombie_walk1', 0, 566, 50, 80),
    ('zombie_walk2', 50, 566, 50, 80),
    ('zombie_walk3', 100, 566, 50, 80),
    ('zombie_walk4', 150, 566, 50, 80),
    ('zombie_atk1', 200, 566, 98, 80),
    ('zombie_atk2', 298, 566, 98, 80),
    ('zombie_atk3', 396, 566, 98, 80),
    ('zombie_fall1', 988, 566, 50, 80),
    ('zombie_fall2', 1038, 566, 50, 80),
]

ANIMS = {
    'walk':   ((['zombie_walk1', 'zombie_walk2', 'zombie_walk3', 'zombie_walk4'],), 5),
    'attack': ((['zombie_atk1', 'zombie_atk2', 'zombie_atk3'],), 9),
    'fall':   ((['zombie_fall1', 'zombie_fall2'],), 4),
}


def init(obj, params):
    """Инициализация зомби."""
    obj['speed'] = 0.4
    obj['hitW'] = False
    return ['zombie_walk1', 'zombie_walk2', 'zombie_walk3', 'zombie_walk4', 
            'zombie_atk1', 'zombie_atk2', 'zombie_atk3', 'zombie_fall1', 'zombie_fall2']


def behave(obj, input_data, ctx):
    """Логика зомби: патрулирование."""
    if ctx is None:
        return
    
    # Гравитация
    obj['vy'] = min(7, obj['vy'] + 0.45)
    
    # Движение по X
    obj['x'] += obj['vx']
    
    # Если уперся в стену и скорость упала до 0, разворачиваемся
    if obj.get('hitW', False) and obj['vx'] == 0:
        obj['vx'] = -0.4 if obj['face'] > 0 else 0.4
        obj['face'] = 1 if obj['vx'] > 0 else -1
    
    # Движение по Y и проверка земли
    pb = obj['y'] + obj['h']
    obj['y'] += obj['vy']
    
    # Проверка земли
    obj['onG'] = False
    gy = int((obj['y'] + obj['h'] + 2) // ctx.TS)
    gx_left = int(obj['x'] // ctx.TS)
    gx_right = int((obj['x'] + obj['w']) // ctx.TS)
    
    for gx in range(gx_left, gx_right + 1):
        if 0 <= gy < ctx.ROWS and ctx.grid[gy][gx] in (1, 2):
            if obj['vy'] >= 0:
                obj['y'] = gy * ctx.TS - obj['h']
                obj['vy'] = 0
                obj['onG'] = True
            break
    
    if obj['onG']:
        # Проверяем точку впереди по направлению движения
        fx = obj['x'] + obj['w'] + 1 if obj['vx'] > 0 else obj['x'] - 1
        gy = int((obj['y'] + obj['h'] + 2) // ctx.TS)
        gx = int(fx // ctx.TS)
        
        # Есть ли земля впереди?
        ground = 0 <= gy < ctx.ROWS and ctx.grid[gy][gx] in (1, 2)
        
        # Есть ли шип впереди?
        spike_ahead = False
        if hasattr(ctx, 'spikes'):
            for s in ctx.spikes:
                if pygame.Rect(s['x'], s['y'], 16, 16).collidepoint(fx, obj['y'] + obj['h'] - 4):
                    spike_ahead = True
                    break
        
        # Если впереди нет земли, есть шип или стена — разворачиваемся
        if not ground or spike_ahead or obj.get('hitW', False):
            obj['vx'] = -obj['vx']
            obj['face'] = 1 if obj['vx'] > 0 else -1


def transform(obj):
    """Обработка коллизий для зомби."""
    for col in obj.get('collisions', []):
        target = col.get('target')
        normal = col.get('normal', (0, 0))
        depth = col.get('depth', 0)
        
        # Отталкивание от игрока
        if target and hasattr(target, 'layer') and target['layer'] == 1:  # Игрок
            target['vx'] += normal[0] * 0.5
            target['vy'] += normal[1] * 0.5
        
        # Отталкивание от других врагов
        if target and hasattr(target, 'layer') and target['layer'] == 2:  # Другой враг
            obj['vx'] += normal[0] * 0.3
            obj['vy'] += normal[1] * 0.3
    
    obj['collisions'] = []


def get_sprite(obj):
    """Возвращает имя текущего спрайта."""
    state = 'walk'
    
    if state not in ANIMS:
        state = 'walk'
    
    anim_data = ANIMS[state]
    sequences = anim_data[0]
    speed = anim_data[1] if len(anim_data) > 1 else 1
    
    seq = sequences[0]
    frame_idx = (obj.get('t', 0) // speed) % len(seq)
    return seq[frame_idx]


# Регистрируем тип объекта
register_object_type(
    name='zombie',
    init_func=init,
    behave_func=behave,
    transform_func=transform,
    get_sprite_func=get_sprite,
    hitbox=HITBOX,
    anchor_type=ANCHOR_TYPE,
    layer=LAYER,
    tags=['solid', 'damage'],
)
