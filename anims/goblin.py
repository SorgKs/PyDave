#!/usr/bin/env python3
# anims/goblin.py — гоблин: анимации и логика
import pygame
import random
import math

NAME = 'goblin'
FALLBACK = 'goblin_walk1'  # <-- ВАЖНО: fallback должен быть в списке ATLAS
DEFAULT = 'walk'
HITBOX = (12, 13)

# Координаты спрайтов гоблина в dave.png (y=730)
ATLAS = [
    ('goblin_walk1', 0, 730, 48, 48),
    ('goblin_walk2', 48, 730, 48, 48),
    ('goblin_walk3', 96, 730, 48, 48),
    ('goblin_walk4', 144, 730, 48, 48),
    ('goblin_atk1', 192, 730, 48, 48),
    ('goblin_atk2', 240, 730, 48, 48),
    ('goblin_atk3', 288, 730, 48, 48),
]

ANIMS = {
    'walk':   ((['goblin_walk1', 'goblin_walk2', 'goblin_walk3', 'goblin_walk4'],), 8),
    'attack': ((['goblin_atk1', 'goblin_atk2', 'goblin_atk3'],), 10),
}

def anim_state(e):
    # Гоблин летает, поэтому всегда в состоянии walk
    return 'walk'

def update(e, ctx):
    e['t'] += 1
    
    # Горизонтальное движение
    speed = 0.6
    e['vx'] = speed if e.get('face', 1) > 0 else -speed
    
    # Вертикальное движение (синусоида)
    e['vy'] = math.sin(e['t'] * 0.05 + e.get('seed', 0)) * 0.5
    
    # Случайный разворот
    if random.random() < 0.01:
        e['face'] = -e.get('face', 1)
    
    # Применяем движение
    ctx.move_x(e)
    
    # Гоблин не подчиняется гравитации, просто двигаем по Y
    e['y'] += e['vy']
    
    # Ограничиваем в пределах уровня
    if e['y'] < 50:
        e['y'] = 50
        e['vy'] = abs(e['vy'])
    if e['y'] > ctx.ROWS * ctx.TS - 50:
        e['y'] = ctx.ROWS * ctx.TS - 50
        e['vy'] = -abs(e['vy'])