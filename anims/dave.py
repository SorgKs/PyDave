#!/usr/bin/env python3
# anims/dave.py — Дэйв: атлас webdave (y=0), анимации, физика
import pygame

NAME = 'dave'
FALLBACK = 'dave_idle'
DEFAULT = 'idle'
HITBOX = (36, 48)

ATLAS = [
    # name, x, y, w, h  — все на y=0 (первая строка атласа)
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

def anim_state(p):
    if p.get('aim_up', False):
        return 'aimup'
    if p.get('aim_down', False):
        return 'aimdown'
    if p['cool'] > 4:
        return 'shoot'
    if not p['onG']:
        return 'fall' if p['vy'] > 0 else 'jump'
    if abs(p['vx']) > .3:
        return 'walk'
    return 'idle'

def update(p, pressed, held, ctx):
    # --- УПРАВЛЕНИЕ ---
    left = held[pygame.K_LEFT] or held[pygame.K_a]
    right = held[pygame.K_RIGHT] or held[pygame.K_d]
    jump = pygame.K_SPACE in pressed
    p['aim_up'] = held[pygame.K_UP] or held[pygame.K_w]
    p['aim_down'] = held[pygame.K_DOWN] or held[pygame.K_s]
    drop = p['aim_down'] and jump

    # --- ДВИЖЕНИЕ ---
    acc = .5 if p['onG'] else .3
    vmax = 2.3
    if left:
        p['vx'] = max(p['vx'] - acc, -vmax)
        p['face'] = -1
    elif right:
        p['vx'] = min(p['vx'] + acc, vmax)
        p['face'] = 1
    else:
        f = .4 if p['onG'] else .1
        if p['vx'] > 0:
            p['vx'] = max(0, p['vx'] - f)
        elif p['vx'] < 0:
            p['vx'] = min(0, p['vx'] + f)

    # --- ТАЙМЕРЫ ---
    if p['drop'] > 0:
        p['drop'] -= 1
    if p['inv'] > 0:
        p['inv'] -= 1
    if p['cool'] > 0:
        p['cool'] -= 1

    # --- ФИЗИКА ---
    ctx.update_player_physics(p)

    # --- ПРЫЖОК ---
    if jump and p['onG'] and p['drop'] <= 0:
        p['vy'] = -6.5
        ctx.play('jump')
        ctx.add_parts(p['x'] + 6, p['y'] + 28, 5, '#8a7f9a', 1, .05)

    # --- СПРЫГИВАНИЕ ---
    if drop and p['onG'] and p.get('drop', 0) <= 0:
        ty = int((p['y'] + p['h'] + 1) // ctx.TS)
        on_plat = False
        for tx in range(int(p['x'] // ctx.TS), int((p['x'] + p['w']) // ctx.TS) + 1):
            if 0 <= ty < ctx.ROWS and ctx.grid[ty][tx] == 2 and ctx.tile_at(tx, ty) != 1:
                on_plat = True
                break
        if on_plat:
            p['drop'] = 12
            p['onG'] = False
            p['vy'] = 1.0

    # --- ЗВУК ПРИЗЕМЛЕНИЯ ---
    if p['onG'] and not p['wasG']:
        ctx.play('land')
    p['wasG'] = p['onG']

    # --- ВЫСТРЕЛ ---
    if (held[pygame.K_x] or held[pygame.K_j] or held[pygame.K_k]) and p['cool'] <= 0:
        p['cool'] = 18
        ctx.play('shoot')
        ctx.shake(1.2)
        p['vx'] -= p['face'] * 1.8
        import aim
        target, hit_pos, hit_type = aim.find_target_in_cone(
            p, ctx.enemies, ctx.grid, ctx.ROWS, ctx.COLS
        )
        if target:
            target['hp'] -= 1
            target['flash'] = 8
            ctx.play('hit')
            ctx.add_parts(hit_pos[0], hit_pos[1], 10, '#ffd23f', 2.0)
            if target['hp'] <= 0:
                # Без начисления очков
                ctx.play('kill')
                ctx.add_parts(hit_pos[0], hit_pos[1], 20, '#ff4444', 3.0)
                if target in ctx.enemies:
                    ctx.enemies.remove(target)
        elif hit_type in ('wall', 'floor'):
            ctx.add_parts(hit_pos[0], hit_pos[1], 6, '#ffd23f', 1.5)

    # --- ШИПЫ ---
    for s in ctx.spikes:
        if ctx.p_rect(p).colliderect(pygame.Rect(s['x'], s['y'], 16, 16).inflate(-4, -6).move(0, 1)):
            ctx.hurt(s['x'] + 8)
            p['vy'] = -5
            break

    # --- ПАДЕНИЕ ЗА КАРТУ ---
    if p['y'] > ctx.ROWS * ctx.TS + 24:
        ctx.kill()