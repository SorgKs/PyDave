#!/usr/bin/env python3
# main.py — DAVE DANGEROUS: игровой цикл по api-decisions
import math
import random
import warnings
import sys

warnings.filterwarnings('ignore')

try:
    import pygame
except ImportError:
    sys.exit('нужен pygame:  pip install pygame')

from config import TS, SCALE, VW, VH, WW, WH, FPS, RATE, MUSIC_VOL
from assets import load_all_sprites, load_all_sounds, make_white_variant
from strings import *
import levels
import level as lvl
import tilemap
from tiles import load_tiles
from surface_map import build_surface_map

from engine import physics, render, objects as eng_objects
from anims import behave, transform
import anims.dave
import anims.zombie  # noqa: F401
import anims.goblin  # noqa: F401
import anims.ghost  # noqa: F401
import anims.skull  # noqa: F401
import anims.item_gem  # noqa: F401

import text
text.init_font()

AUDIO = False
try:
    import pygame.mixer
    AUDIO = True
except Exception:
    pass

if AUDIO:
    try:
        pygame.mixer.pre_init(RATE, -16, 1, 512)
        pygame.init()
        if not pygame.mixer.get_init():
            AUDIO = False
    except Exception:
        AUDIO = False
else:
    pygame.init()

screen = pygame.display.set_mode((WW, WH))
pygame.display.set_caption(WINDOW_TITLE)
clock = pygame.time.Clock()

# ============================================================================
# АССЕТЫ
# ============================================================================

# Типы уже зарегистрированы → sprites_map агрегируется в assets
I = load_all_sprites()
TILES = load_tiles()
I.update(TILES)

WHITE = {
    n: make_white_variant(I[n])
    for n in I
    if n.startswith(('zombie', 'ghost', 'goblin', 'bat'))
}

SFX, MUSIC = (load_all_sounds() if AUDIO else ({}, None))
MUTED = [False]


def play(n):
    if AUDIO and not MUTED[0] and SFX.get(n):
        SFX[n].play()


# ============================================================================
# УРОВЕНЬ
# ============================================================================

tilemap.init_tilemap()
surface_grid, ROWS, COLS = build_surface_map(verbose=False)
physics.init_physics(surface_grid, ROWS, COLS)

level_data = levels.parse_objects(lvl.MAP)
all_objects = level_data['objects']
player_obj = level_data['player']
spikes = level_data['spikes']
torches = level_data['torches']
hearts = level_data['hearts']
door = level_data['door']
doors_decor = level_data['doors_decor']
spawn_pos = level_data['spawn_pos']

cam_x = cam_y = 0.0
shake = 0.0
state, state_t, gtime = 'title', 0, 0
parts, texts = [], []
view = pygame.Surface((VW, VH))
# ключ спрайта за кадр: id(obj) → str
frame_sprites = {}
# сцена смерти от зомби: замороженные спрайты + таймер анимации
death_scene = None


# ============================================================================
# ВВОД → токены keys (l+/l=, j+, …)
# ============================================================================

# (pygame key, action code)
_HOLD_MAP = (
    (pygame.K_LEFT, 'l'), (pygame.K_a, 'l'),
    (pygame.K_RIGHT, 'r'), (pygame.K_d, 'r'),
    (pygame.K_SPACE, 'j'),
    (pygame.K_UP, 'u'), (pygame.K_w, 'u'),
    (pygame.K_DOWN, 'd'), (pygame.K_s, 'd'),
    (pygame.K_x, 's'), (pygame.K_j, 's'), (pygame.K_k, 's'),
)


def build_keys(pressed, held):
    """Семантический снимок действий: 'l+', 'l=', 'j+', …"""
    keys = set()
    # edge: только коды из pressed
    edge_codes = set()
    for pk in pressed:
        for pk_map, code in _HOLD_MAP:
            if pk == pk_map:
                edge_codes.add(code)
    for code in edge_codes:
        keys.add(code + '+')

    held_codes = set()
    for pk_map, code in _HOLD_MAP:
        if held[pk_map]:
            held_codes.add(code)
    for code in held_codes:
        keys.add(code + '=')
    return keys


# ============================================================================
# ИГРА
# ============================================================================

def reset_game():
    global state, state_t, all_objects, player_obj, death_scene
    global spikes, torches, hearts, door, doors_decor, spawn_pos

    data = levels.parse_objects(lvl.MAP)
    all_objects = data['objects']
    player_obj = data['player']
    spikes = data['spikes']
    torches = data['torches']
    hearts = data['hearts']
    door = data['door']
    doors_decor = data['doors_decor']
    spawn_pos = data['spawn_pos']

    parts.clear()
    texts.clear()
    death_scene = None
    state = 'play'
    state_t = 0


def add_parts(x, y, n, col, spd=0.12, g=0.005):
    """Частицы: x,y,vx,vy,g в тайлах; sz — пиксели при отрисовке."""
    for _ in range(n):
        a = random.random() * 6.2832
        v = (0.3 + random.random()) * spd
        parts.append({
            'x': float(x), 'y': float(y),
            'vx': math.cos(a) * v,
            'vy': math.sin(a) * v - spd * 0.25,
            'g': g,
            'life': 0,
            'max': 25 + random.random() * 20,
            'col': col,
            'sz': 1 + random.random() * 2,
        })


def add_text(x, y, t, col='#fff'):
    """Всплывающий текст: x,y в тайлах."""
    texts.append({'x': float(x), 'y': float(y), 'txt': t, 'col': col, 'life': 0})


def shake_amt(v):
    global shake
    shake = max(shake, v)


def kill_player():
    global state, state_t, death_scene
    if state != 'play':
        return
    play('die')
    shake_amt(9)
    add_parts(player_obj['x'], player_obj['y'], 26, '#e23b4e', 0.2)
    death_scene = None
    state = 'gameover'
    state_t = 0


def start_zombie_death(killer):
    """Смерть от зомби: заморозка сцены, анимация поверх (webdave playerDeathZombie)."""
    global state, state_t, death_scene, frame_sprites
    if state != 'play':
        return
    play('die')
    shake_amt(9)
    add_parts(player_obj['x'], player_obj['y'], 26, '#e23b4e', 0.2)

    frozen = {
        id(player_obj): frame_sprites.get(id(player_obj)),
    }
    if killer is not None:
        frozen[id(killer)] = frame_sprites.get(id(killer))

    death_scene = {
        'frozen': frozen,
        'cx': player_obj['x'],
        'cy': player_obj['y'] - player_obj['h'] * 0.5,
        't': 0,
    }
    state = 'death_zombie'
    state_t = 0


def _death_zombie_frame():
    """Текущий кадр анимации смерти от зомби."""
    if not death_scene:
        return None
    frames = anims.dave.DEATH_ZOMBIE_FRAMES
    speed = anims.dave.DEATH_ZOMBIE_SPEED
    idx = min(death_scene['t'] // speed, len(frames) - 1)
    return frames[idx]


def _death_zombie_finished():
    if not death_scene:
        return False
    n = len(anims.dave.DEATH_ZOMBIE_FRAMES)
    total = n * anims.dave.DEATH_ZOMBIE_SPEED + anims.dave.DEATH_ZOMBIE_HOLD
    return death_scene['t'] >= total


def _shot_particles(fx):
    """Частицы в точке попадания (тайлы); 2/3 / 1/3 цвета; разлёт к стрелку."""
    if fx.get('kind') not in ('enemy', 'wall'):
        return
    x1, y1 = fx['x'], fx['y']
    if fx.get('dir_x') is not None:
        base = math.atan2(fx.get('dir_y', 0), fx['dir_x'])
    else:
        face = fx.get('face', 1)
        base = math.pi if face > 0 else 0.0
    colors = fx.get('colors') or ('#000000', '#ffffff')
    c0 = colors[0]
    c1 = colors[1] if len(colors) > 1 else colors[0]
    n = 36
    n0 = (n * 2) // 3
    for i in range(n):
        col = c0 if i < n0 else c1
        # скорости в тайлах/кадр (короткая дистанция, широкий угол)
        spd = 0.035 + random.random() * 0.055
        phi = (random.random() - 0.5) * 3.8
        ang = base + phi
        parts.append({
            'x': float(x1), 'y': float(y1),
            'vx': spd * math.cos(ang),
            'vy': spd * math.sin(ang),
            'g': 0.001,
            'life': 0,
            'max': 18 + random.random() * 12,
            'col': col,
            'sz': 1 + random.random() * 2,
        })


def _handle_dave_side_effects(obj):
    if obj.get('pending_jump_sfx'):
        play('jump')
        add_parts(obj['x'], obj['y'], 5, '#8a7f9a', 0.06, 0.003)
        obj['pending_jump_sfx'] = False
    if obj.get('pending_land_sfx'):
        play('land')
        obj['pending_land_sfx'] = False
    if obj.get('pending_shoot'):
        fx = anims.dave.fire_shot_if_ready(obj, surface_grid, all_objects)
        if fx is not None:
            play('shoot')
            shake_amt(1.2)
            _shot_particles(fx)
            if fx.get('kind') == 'enemy':
                play('hit')
            obj['pending_shot_fx'] = None
    if obj.get('pending_reload_sfx'):
        play('reload')
        obj['pending_reload_sfx'] = False
    if obj.get('pending_no_ammo_sfx'):
        play('noAmmo')
        obj['pending_no_ammo_sfx'] = False


def update(pressed, held):
    global state, state_t, gtime, cam_x, cam_y, shake, frame_sprites, death_scene

    gtime += 1
    state_t += 1

    if pygame.K_m in pressed:
        MUTED[0] = not MUTED[0]
        if AUDIO and MUSIC:
            MUSIC.set_volume(0 if MUTED[0] else MUSIC_VOL)

    if pygame.K_r in pressed and state in ('play', 'gameover', 'win', 'death_zombie'):
        reset_game()

    if pygame.K_p in pressed:
        if state == 'play':
            state = 'pause'
            state_t = 0
        elif state == 'pause':
            state = 'play'

    if state == 'title':
        if pygame.K_RETURN in pressed or pygame.K_SPACE in pressed:
            reset_game()
    elif state == 'death_zombie':
        death_scene['t'] += 1
        if _death_zombie_finished():
            death_scene = None
            state = 'gameover'
            state_t = 0
    elif state in ('gameover', 'win'):
        if pygame.K_RETURN in pressed:
            reset_game()
    elif state == 'play':
        keys = build_keys(pressed, held)
        empty_keys = set()

        # A. behave
        for obj in all_objects:
            obj['t'] = obj.get('t', 0) + 1
            if obj.get('flash', 0) > 0:
                obj['flash'] -= 1
            k = keys if obj is player_obj else empty_keys
            behave(obj, k, surface_grid, all_objects)
            if obj is player_obj:
                _handle_dave_side_effects(obj)

        # B. physics
        physics.update_physics(all_objects)

        # C. transform каждый кадр
        frame_sprites = {}
        for obj in all_objects:
            if obj.get('taken'):
                continue
            sprite_key = transform(obj)
            if sprite_key:
                frame_sprites[id(obj)] = sprite_key

        if player_obj.get('dead'):
            killer = player_obj.pop('death_killer', None)
            if killer and killer.get('type') == 'zombie':
                start_zombie_death(killer)
            else:
                kill_player()
            player_obj['dead'] = False

        # Смерть врагов (HP==0 после get_shot в transform)
        for e in all_objects:
            if e is player_obj or not e.get('dead'):
                continue
            if 'enemy' not in e.get('tags', []):
                continue
            play('kill')
            add_parts(e['x'], e['y'], 16, '#7fff8a', 0.15)
            add_parts(e['x'], e['y'], 8, '#e23b4e', 0.1)

        # Дверь (координаты в тайлах)
        if door is not None and state == 'play':
            pr_px = eng_objects.get_hitbox_rect(player_obj, ts=TS)
            door_rect = pygame.Rect(
                int(door['x'] * TS + 2), int(door['y'] * TS + 6), 12, 26)
            if pr_px.colliderect(door_rect):
                if door['open'] >= 1 and state_t > 30:
                    state = 'win'
                    state_t = 0

        # Убрать предметы и мёртвых врагов
        all_objects[:] = [
            o for o in all_objects
            if not o.get('taken')
            and not (o is not player_obj and o.get('dead') and 'enemy' in o.get('tags', []))
        ]

    for p in parts[:]:
        p['x'] += p['vx']
        p['y'] += p['vy']
        p['vy'] += p['g']
        p['life'] += 1
        if p['life'] > p['max']:
            parts.remove(p)

    for t in texts[:]:
        t['y'] -= 0.025  # тайлы/кадр
        t['life'] += 1
        if t['life'] > 60:
            texts.remove(t)

    shake *= 0.86
    if shake < 0.2:
        shake = 0

    if door is not None and 0 < door['open'] < 1:
        door['open'] = min(1.0, door['open'] + 0.04)

    if state == 'title':
        tx = 40 + (math.sin(gtime * 0.004) * 0.5 + 0.5) * (COLS * TS - VW - 80)
        ty = 32 + math.sin(gtime * 0.002) * 20
        cam_x += (tx - cam_x) * 0.1
        cam_y += (ty - cam_y) * 0.12
    elif state != 'death_zombie':
        # Камера от якоря игрока (тайлы → пиксели)
        px = player_obj['x'] * TS
        py = player_obj['y'] * TS
        tx = px - VW / 2 + player_obj['face'] * 28
        ty = py - VH / 2 - 40
        cam_x += (tx - cam_x) * 0.1
        cam_y += (ty - cam_y) * 0.12
        cam_x = max(0, min(cam_x, COLS * TS - VW))
        cam_y = max(0, min(cam_y, ROWS * TS - VH))


def blit(surf, im, x, y, flip=False, alpha=None):
    if flip:
        im = pygame.transform.flip(im, True, False)
    if alpha is not None:
        im.set_alpha(alpha)
    surf.blit(im, (int(round(x)), int(round(y))))


def render_frame():
    view.fill((0, 0, 0))
    ox = int(cam_x + (random.random() - 0.5) * shake)
    oy = int(cam_y + (random.random() - 0.5) * shake)

    render.render_tilemap(view, tilemap.grid, ox, oy, TS, I, VW, VH)

    if 'spike' in I:
        for s in spikes:
            sx, sy = s['x'] * TS, s['y'] * TS
            if ox - 16 <= sx <= ox + VW + 16:
                view.blit(I['spike'], (sx - ox, sy - oy))

    for t in torches:
        x, y = t['x'] * TS - ox, t['y'] * TS - oy
        flick = math.sin(gtime * 0.3 + t['seed']) * 0.5 + math.sin(gtime * 0.13 + t['seed'] * 2) * 0.5
        if 'glow_torch' in I:
            view.blit(I['glow_torch'], (x + 8 - 26, y + 7 - 26), special_flags=pygame.BLEND_ADD)
        pygame.draw.rect(view, text.C('#5a3a20'), (x + 7, y + 9, 2, 5))
        pygame.draw.rect(view, text.C('#3a2412'), (x + 6, y + 13, 4, 2))
        fh = 5 + flick * 1.5
        pygame.draw.polygon(view, text.C('#ff8c2e'),
                            [(x + 5, y + 9), (x + 8, y + 9 - fh * 1.6), (x + 11, y + 9)])
        pygame.draw.polygon(view, text.C('#ffd23f'),
                            [(x + 6, y + 9), (x + 8, y + 9 - fh), (x + 10, y + 9)])
        pygame.draw.rect(view, text.C('#fff3b0'), (x + 7, y + 7, 2, 2))

    for dx, dy in doors_decor:
        if 'door_closed' in I:
            view.blit(I['door_closed'], (dx * TS - ox, dy * TS - oy))

    if door is not None:
        door_name = 'door_open' if door['open'] > 0 else 'door_closed'
        if door_name in I:
            view.blit(I[door_name], (door['x'] * TS - ox, door['y'] * TS - oy))

    if 'heart' in I:
        for h in hearts:
            if h.get('taken'):
                continue
            s = 1 + 0.08 * math.sin(gtime * 0.15)
            im = pygame.transform.scale(I['heart'], (int(16 * s), int(16 * s)))
            hx, hy = h['x'] * TS, h['y'] * TS
            view.blit(im, (hx - ox - im.get_width() // 2 + 8,
                           hy - oy - im.get_height() // 2 + 8))

    # Объекты (кроме скрытого игрока на title/gameover)
    frozen = death_scene.get('frozen', {}) if death_scene else {}
    for obj in all_objects:
        if obj.get('taken'):
            continue
        if obj is player_obj and state in ('title', 'gameover'):
            continue
        if obj is player_obj and state == 'play' and obj.get('inv', 0) > 0 and gtime % 6 < 3:
            continue

        key = frozen.get(id(obj), frame_sprites.get(id(obj)))
        if not key or key not in I:
            continue
        im = WHITE[key] if obj.get('flash', 0) > 0 and key in WHITE else I[key]
        sw, sh = im.get_width(), im.get_height()
        rx, ry = eng_objects.get_sprite_render_pos(obj, ox, oy, sw, sh, TS)

        if obj.get('type') == 'ghost' and 'glow_ghost' in I:
            view.blit(I['glow_ghost'], (rx - 8, ry - 8), special_flags=pygame.BLEND_ADD)

        blit(view, im, rx, ry, obj.get('face', 1) < 0)

    # Анимация смерти от зомби поверх замороженной сцены
    if state == 'death_zombie' and death_scene:
        dkey = _death_zombie_frame()
        if dkey and dkey in I:
            im = I[dkey]
            sw, sh = im.get_width(), im.get_height()
            cx = death_scene['cx'] * TS
            cy = death_scene['cy'] * TS
            view.blit(im, (int(cx - sw / 2 - ox), int(cy - sh / 2 - oy)))

    for p in parts:
        a = max(0, 1 - p['life'] / p['max'])
        col = pygame.Color(p['col'])
        col.r = int(col.r * a)
        col.g = int(col.g * a)
        col.b = int(col.b * a)
        # тайлы → пиксели только здесь
        pygame.draw.rect(
            view, col,
            (p['x'] * TS - ox, p['y'] * TS - oy, p['sz'], p['sz']))

    pygame.transform.scale(view, (WW, WH), screen)

    if text.FONT_OK:
        for t in texts:
            im = text.font(16).render(t['txt'], True, pygame.Color(t['col']))
            im.set_alpha(int(255 * max(0, 1 - t['life'] / 60)))
            screen.blit(im, ((t['x'] * TS - ox) * SCALE, (t['y'] * TS - oy) * SCALE))

    draw_hud()
    draw_overlays()


def overlay(col=(5, 3, 12, 150)):
    s = pygame.Surface((WW, WH), pygame.SRCALPHA)
    s.fill(col)
    screen.blit(s, (0, 0))


def draw_hud():
    """Иконка патронов в левом верхнем углу экрана."""
    if state != 'play':
        return
    ammo = player_obj.get('ammo', 0)
    key = 'ammo_%d' % ammo
    if key not in I:
        return
    im = I[key]
    screen.blit(im, (int(20 * SCALE), int(20 * SCALE)))


def draw_overlays():
    blink = gtime % 70 < 45
    if state == 'title':
        overlay()
        text.text_out(screen, TITLE_BIG, WW // 2, 165, 76, '#ffd23f', True)
        text.text_out(screen, TITLE_SUB, WW // 2, 215, 32, '#8fd3ff', True)
        text.text_out(screen, TITLE_HINT_1, WW // 2, 300, 24, '#cfc8e8', True)
        text.text_out(screen, TITLE_HINT_2, WW // 2, 332, 24, '#cfc8e8', True)
        text.text_out(screen, TITLE_HINT_3, WW // 2, 380, 22, '#9a90b8', True)
        if blink:
            text.text_out(screen, TITLE_PROMPT, WW // 2, 450, 36, '#ffd23f', True)
    elif state == 'pause':
        overlay()
        text.text_out(screen, PAUSE_TITLE, WW // 2, 270, 60, '#8fd3ff', True)
    elif state == 'gameover':
        overlay((30, 5, 10, 180))
        text.text_out(screen, "GAME OVER", WW // 2, 235, 68, '#e23b4e', True)
        if blink:
            text.text_out(screen, "Нажми R для рестарта", WW // 2, 320, 28, '#fff', True)
    elif state == 'win':
        overlay((5, 15, 10, 170))
        text.text_out(screen, "YOU WIN!", WW // 2, 205, 66, '#7fff8a', True)
        text.text_out(screen, "Уровень пройден", WW // 2, 258, 28, '#cfc8e8', True)
        if blink:
            text.text_out(screen, "Нажми R для рестарта", WW // 2, 350, 28, '#fff', True)


def main():
    running = True
    while running:
        clock.tick(FPS)
        pressed = set()
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    running = False
                pressed.add(e.key)
        held = pygame.key.get_pressed()
        update(pressed, held)
        render_frame()
        pygame.display.flip()
    pygame.quit()


if __name__ == '__main__':
    main()
