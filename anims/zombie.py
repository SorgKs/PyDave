#!/usr/bin/env python3
# anims/zombie.py — зомби: патруль
import pygame

NAME = 'zombie'
FALLBACK = 'zombie_walk1'
DEFAULT = 'walk'
HITBOX = (16, 36)

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

def anim_state(e):
    return 'walk'

def update(e, ctx):
    # Гравитация
    e['vy'] = min(7, e['vy'] + .45)
    pb = e['y'] + e['h']
    
    # Движение по X
    ctx.move_x(e)
    
    # Если уперся в стену и скорость упала до 0, разворачиваемся
    if e.get('hitW', False) and e['vx'] == 0:
        e['vx'] = -.4 if e.get('face', 1) > 0 else .4
        
    # Движение по Y и проверка земли
    ctx.move_y(e, pb)
    
    if e['onG']:
        # Проверяем точку впереди по направлению движения
        fx = e['x'] + e['w'] + 1 if e['vx'] > 0 else e['x'] - 1
        gy = int((e['y'] + e['h'] + 2) // ctx.TS)
        gx = int(fx // ctx.TS)
        
        # Есть ли земля впереди? (1 = стена/пол, 2 = платформа)
        ground = 0 <= gy < ctx.ROWS and ctx.grid[gy][gx] in (1, 2)
        
        # Есть ли шип впереди?
        spike_ahead = any(pygame.Rect(s['x'], s['y'], 16, 16).collidepoint(fx, e['y'] + e['h'] - 4) for s in ctx.spikes)
        
        # Если впереди нет земли, есть шип или стена — разворачиваемся
        if not ground or spike_ahead or e.get('hitW', False):
            e['vx'] = -e['vx']
            e['face'] = 1 if e['vx'] > 0 else -1