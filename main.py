#!/usr/bin/env python3
# main.py — DAVE DANGEROUS: Haunted Mansion
import os, math, random, warnings, sys
warnings.filterwarnings('ignore')

try:
    import pygame
except ImportError:
    sys.exit('нужен pygame:  pip install pygame')

from config import TS, SCALE, VW, VH, WW, WH, FPS, RATE, MUSIC_VOL
from assets import (ASSETS_DIR, load_all_sprites, load_all_sounds,
                    make_white_variant, load_image)
from strings import *
import levels
import level as lvl
import anims
import tilemap
from tiles import load_tiles
from surface_map import build_surface_map
import aim
import text
import physics

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
        if not pygame.mixer.get_init(): AUDIO = False
    except Exception:
        AUDIO = False
else:
    pygame.init()

screen = pygame.display.set_mode((WW, WH))
pygame.display.set_caption(WINDOW_TITLE)
clock = pygame.time.Clock()

# --- Загрузка спрайтов и тайлов ---
I = load_all_sprites()
for mod in anims.ALL:
    for name, *_ in mod.ATLAS:
        if os.path.exists(os.path.join(ASSETS_DIR, 'sprites', name + '.bmp')):
            I[name] = load_image(name + '.bmp', colorkey=True)

TILES = load_tiles()
I.update(TILES)

def have(n): return n in I
WHITE = {n: make_white_variant(I[n]) for n in I if n.startswith(('zombie', 'ghost', 'bat'))}

SFX, MUSIC = (load_all_sounds() if AUDIO else ({}, None))
MUTED = [False]

def play(n):
    if AUDIO and not MUTED[0] and SFX.get(n): SFX[n].play()

# --- 1. ВИЗУАЛЬНАЯ КАРТА (для отрисовки) ---
tilemap.init_tilemap()

# --- 2. ФИЗИЧЕСКАЯ КАРТА (только через surface_map!) ---
surface_grid, ROWS, COLS = build_surface_map(verbose=False)
physics.init_physics(TS, surface_grid, ROWS, COLS)

# --- 3. ОБЪЕКТЫ УРОВНЯ ---
data = levels.parse_objects(lvl.MAP)
spikes = data['spikes']
torches = data['torches']
gems = data['gems']
hearts = data['hearts']
skulls = data['skulls']
enemies = data['enemies']
door = data['door']
key_pos = data['key_pos']
doors_decor = data['doors_decor']
spawn_pos = data['spawn_pos']

# --- 4. ИНИЦИАЛИЗАЦИЯ ВРАГОВ ---
print("[⚙️ INIT] Вызов anims.fix_sizes(enemies)...")
anims.fix_sizes(enemies)
print("[✅ INIT] Враги успешно инициализированы!\n")

# --- Игрок ---
sprite_w = anims.dave.ATLAS[0][2]
sprite_h = anims.dave.ATLAS[0][3]

player = {
    'x': spawn_pos[0],
    'y': spawn_pos[1] - sprite_h,
    'sx': spawn_pos[0],
    'sy': spawn_pos[1] - sprite_h,
    'w': anims.dave.HITBOX[0],
    'h': anims.dave.HITBOX[1],
    'vx': 0.0, 'vy': 0.0,
    'face': 1, 'onG': False, 'wasG': False,
    'coyote': 0, 'jbuf': 0, 'cool': 0, 'inv': 0, 'drop': 0,
    'sprite_w': sprite_w,
    'sprite_h': sprite_h,
    'aim_up': False,
    'aim_down': False,
    'score': 0,
}

state, state_t, gtime = 'title', 0, 0
cam_x = cam_y = 0.0; shake = 0.0; door_hint_cd = 0
parts, texts = [], []
view = pygame.Surface((VW, VH))
ENEMY_DRAW_OFF = {'z': (-4, -4), 'g': (-2, -1), 'b': (-2, -2)}

def reset_player_pos():
    player['x'] = spawn_pos[0]
    player['y'] = spawn_pos[1] - player['sprite_h']
    player['vx'] = player['vy'] = 0

def start_game():
    global state, state_t
    for g in gems: g['taken'] = False
    for h in hearts: h['taken'] = False
    if door is not None:
        door['open'] = 0.0
    enemies.clear()
    parts.clear()
    texts.clear()
    
    enemies.extend(levels.parse_objects(lvl.MAP)['enemies'])
    anims.fix_sizes(enemies)
    
    reset_player_pos()
    player['inv'] = 0
    state = 'play'
    state_t = 0

def add_parts(x, y, n, col, spd, g=.08):
    for _ in range(n):
        a = random.random()*6.2832; v = (.3 + random.random())*spd
        parts.append({'x': x, 'y': y, 'vx': math.cos(a)*v, 'vy': math.sin(a)*v - 1,
                      'g': g, 'life': 0, 'max': 25 + random.random()*20, 'col': col,
                      'sz': 1 + random.random()*2})

def add_text(x, y, t, col='#fff'):
    texts.append({'x': x, 'y': y, 'txt': t, 'col': col, 'life': 0})

def shake_amt(v):
    global shake; shake = max(shake, v)

def kill_player():
    global state, state_t
    if state != 'play': return
    play('die'); shake_amt(9)
    add_parts(player['sx'] + player['sprite_w']//2, player['sy'] + player['sprite_h']//2, 26, '#e23b4e', 3)
    state = 'gameover'; state_t = 0

def hurt_player(src_x):
    if player['inv'] > 0 or state != 'play': return
    player['inv'] = 85
    play('hurt'); shake_amt(5)
    add_parts(player['sx'] + player['sprite_w']//2, player['sy'] + player['sprite_h']//2, 10, '#e23b4e', 2)
    player['vx'] = -3 if player['sx'] + player['sprite_w']//2 < src_x else 3
    player['vy'] = -3.5
    kill_player()

class _Ctx: pass
CTX = _Ctx()
CTX.TS, CTX.ROWS, CTX.COLS, CTX.grid, CTX.spikes, CTX.enemies = TS, ROWS, COLS, surface_grid, spikes, enemies
CTX.tile_at, CTX.move_x, CTX.move_y = physics.tile_at, physics.move_x, physics.move_y
CTX.update_player_physics = physics.update_player_physics
CTX.play, CTX.add_parts, CTX.shake = play, add_parts, shake_amt
CTX.p_rect, CTX.hurt, CTX.kill = physics.p_rect, hurt_player, kill_player

# --- обновление ---
def update(pressed, held):
    global state, state_t, gtime, cam_x, cam_y, shake, door_hint_cd
    gtime += 1; state_t += 1

    if pygame.K_m in pressed:
        MUTED[0] = not MUTED[0]
        if AUDIO and MUSIC: MUSIC.set_volume(0 if MUTED[0] else MUSIC_VOL)

    if pygame.K_r in pressed and state in ('play', 'gameover', 'win'): start_game()
    if pygame.K_p in pressed:
        if state == 'play': state = 'pause'; state_t = 0
        elif state == 'pause': state = 'play'

    if state == 'title':
        if pygame.K_RETURN in pressed or pygame.K_SPACE in pressed: start_game()
    elif state in ('gameover', 'win'):
        if pygame.K_RETURN in pressed: start_game()
    elif state == 'play':
        anims.dave.update(player, pressed, held, CTX)
        
        offset_x = (player['sprite_w'] - player['w']) // 2
        offset_y = (player['sprite_h'] - player['h']) // 2
        player['sx'] = player['x'] - offset_x
        player['sy'] = player['y'] - offset_y
        
        if door is not None:
            p_rect = physics.p_rect_pygame(player)
            if p_rect.colliderect(pygame.Rect(door['x'] + 2, door['y'] + 6, 12, 26)):
                if door['open'] >= 1 and state_t > 30:
                    state = 'win'; state_t = 0
                    
        update_enemies(state == 'title')

    for p in parts[:]:
        p['x'] += p['vx']; p['y'] += p['vy']; p['vy'] += p['g']; p['life'] += 1
        if p['life'] > p['max']: parts.remove(p)

    for t in texts[:]:
        t['y'] -= .4; t['life'] += 1
        if t['life'] > 60: texts.remove(t)

    shake *= .86
    if shake < .2: shake = 0

    if door is not None and 0 < door['open'] < 1:
        door['open'] = min(1.0, door['open'] + .04)
    if door_hint_cd > 0: door_hint_cd -= 1

    if state == 'title':
        tx = 40 + (math.sin(gtime*.004)*.5 + .5)*(COLS*TS - VW - 80)
        ty = 32 + math.sin(gtime*.002)*20
    else:
        tx = player['sx'] + player['sprite_w']//2 - VW/2 + player['face']*28
        ty = player['sy'] + player['sprite_h']//2 - VH/2

    cam_x += (tx - cam_x)*.1; cam_y += (ty - cam_y)*.12
    cam_x = max(0, min(cam_x, COLS*TS - VW)); cam_y = max(0, min(cam_y, ROWS*TS - VH))

def update_enemies(demo):
    for e in enemies:
        e['t'] += 1
        if e['flash'] > 0: e['flash'] -= 1
        
        mod = anims.TYPE_TO_MOD.get(e['type'])
        if not mod:
            continue
            
        mod.update(e, CTX)
        
        if not demo and state == 'play' and player['inv'] <= 0:
            enemy_rect = pygame.Rect(int(e['x']), int(e['y']), e['w'], e['h'])
            player_rect = physics.p_rect_pygame(player)
            if player_rect.colliderect(enemy_rect):
                hurt_player(e['x'] + e['w']/2)

# --- рендер ---
def blit(surf, im, x, y, flip=False, alpha=None):
    if flip: im = pygame.transform.flip(im, True, False)
    if alpha is not None: im.set_alpha(alpha)
    surf.blit(im, (int(round(x)), int(round(y))))

def render():
    view.fill((0, 0, 0))
    ox = int(cam_x + (random.random() - .5)*shake)
    oy = int(cam_y + (random.random() - .5)*shake)

    # --- ОТРИСОВКА ТАЙЛОВ ---
    x0 = max(0, ox // TS)
    x1 = min(tilemap.cols - 1, (ox + VW) // TS + 1)
    y0 = max(0, oy // TS)
    y1 = min(tilemap.rows - 1, (oy + VH) // TS + 1)

    for ty in range(y0, y1 + 1):
        for tx in range(x0, x1 + 1):
            tile_name = tilemap.grid[ty][tx]
            if not tile_name: continue
            im = I.get(tile_name)
            if im is None: continue
            px = tx * TS - ox
            py = ty * TS - oy
            view.blit(im, (int(round(px)), int(round(py))))

    # --- ОБЪЕКТЫ ---
    if 'spike' in I:
        for s in spikes:
            if ox - 16 <= s['x'] <= ox + VW + 16:
                view.blit(I['spike'], (s['x'] - ox, s['y'] - oy))
    if 'skull' in I:
        for sx, sy in skulls:
            view.blit(I['skull'], (sx - ox, sy - oy))

    for t in torches:
        x, y = t['x'] - ox, t['y'] - oy
        flick = math.sin(gtime*.3 + t['seed'])*.5 + math.sin(gtime*.13 + t['seed']*2)*.5
        if 'glow_torch' in I:
            view.blit(I['glow_torch'], (x + 8 - 26, y + 7 - 26), special_flags=pygame.BLEND_ADD)
        pygame.draw.rect(view, text.C('#5a3a20'), (x + 7, y + 9, 2, 5))
        pygame.draw.rect(view, text.C('#3a2412'), (x + 6, y + 13, 4, 2))
        fh = 5 + flick*1.5
        pygame.draw.polygon(view, text.C('#ff8c2e'), [(x + 5, y + 9), (x + 8, y + 9 - fh*1.6), (x + 11, y + 9)])
        pygame.draw.polygon(view, text.C('#ffd23f'), [(x + 6, y + 9), (x + 8, y + 9 - fh), (x + 10, y + 9)])
        pygame.draw.rect(view, text.C('#fff3b0'), (x + 7, y + 7, 2, 2))

    for dx, dy in doors_decor:
        if 'door_orig' in I:
            view.blit(I['door_orig'], (dx - ox - 8, dy - oy - 16))
        elif 'door_closed' in I:
            view.blit(I['door_closed'], (dx - ox, dy - oy))

    if door is not None:
        if 'door_orig' in I:
            view.blit(I['door_orig'], (door['x'] - ox - 8, door['y'] - oy - 16))
        else:
            door_name = 'door_open' if door['open'] > 0 else 'door_closed'
            if door_name in I:
                view.blit(I[door_name], (door['x'] - ox, door['y'] - oy))

    if 'gem' in I:
        for g in gems:
            if g['taken']: continue
            bob = math.sin(gtime*.08 + g['seed'])*2
            view.blit(I['gem'], (g['x'] - ox, g['y'] - oy + bob))

    if 'heart' in I:
        for h in hearts:
            if h['taken']: continue
            s = 1 + .08*math.sin(gtime*.15)
            im = pygame.transform.scale(I['heart'], (int(16*s), int(16*s)))
            view.blit(im, (h['x'] - ox - im.get_width()//2 + 8, h['y'] - oy - im.get_height()//2 + 8))

    gh_alpha = int(200 + 40*math.sin(gtime*.1))
    for e in enemies:
        if e['x'] < ox - 60 or e['x'] > ox + VW + 60: continue
        
        flip = e['face'] < 0
        alpha = None
        mod = anims.TYPE_TO_MOD[e['type']]
        nm = anims.frame(mod, mod.anim_state(e), gtime, have)
        
        if nm in I:
            im = WHITE.get(nm, I[nm]) if e['flash'] > 0 else I[nm]
        else:
            continue
            
        # 🔥 ЛОГИРОВАНИЕ КАЖДЫЕ 5 СЕКУНД (300 кадров при 60 FPS) ТОЛЬКО ПРИ ОТРИСОВКЕ
        if e['type'] == 'z' and gtime % 300 == 0:
            print(f"[🧟 RENDER] t={gtime//60}s | x={e['x']:.1f}, y={e['y']:.1f}, "
                  f"vx={e['vx']:.2f}, vy={e['vy']:.2f}, onG={e['onG']}, "
                  f"sprite={nm}, flash={e['flash']}")
            
        if e['type'] == 'g' and 'glow_ghost' in I:
            alpha = gh_alpha
            view.blit(I['glow_ghost'], (e['x'] - ox - 8, e['y'] - oy - 8), special_flags=pygame.BLEND_ADD)
        dx, dy = ENEMY_DRAW_OFF.get(e['type'], (0, 0))
        blit(view, im, e['x'] - ox + dx, e['y'] - oy + dy, flip, alpha)

    # --- ОТРИСОВКА ДЕЙВА ---
    if state not in ('title', 'gameover'):
        p = player
        if not (p['inv'] > 0 and gtime % 6 < 3 and state == 'play'):
            nm = anims.frame(anims.dave, anims.dave.anim_state(p), gtime, have)
            if nm in I:
                im = I[nm]
                w, h = im.get_width(), im.get_height()
                if w != p['sprite_w'] or h != p['sprite_h']:
                    p['sprite_w'] = w
                    p['sprite_h'] = h
                oy2 = -1 if (abs(p['vx']) > .3 and p['onG'] and math.sin(gtime*.4) > .5) else 0
                blit(view, im, p['sx'] - ox, p['sy'] - oy + oy2, p['face'] < 0)

    # --- ЧАСТИЦЫ ---
    for p in parts:
        a = max(0, 1 - p['life']/p['max'])
        col = pygame.Color(p['col'])
        col.r = int(col.r*a); col.g = int(col.g*a); col.b = int(col.b*a)
        pygame.draw.rect(view, col, (p['x'] - ox, p['y'] - oy, p['sz'], p['sz']))

    # --- МАСШТАБИРОВАНИЕ НА ЭКРАН ---
    pygame.transform.scale(view, (WW, WH), screen)

    # --- ТЕКСТЫ ---
    if text.FONT_OK:
        for t in texts:
            im = text.font(16).render(t['txt'], True, pygame.Color(t['col']))
            im.set_alpha(int(255*max(0, 1 - t['life']/60)))
            screen.blit(im, ((t['x'] - ox)*SCALE, (t['y'] - oy)*SCALE))

    draw_overlays()

def overlay(col=(5, 3, 12, 150)):
    s = pygame.Surface((WW, WH), pygame.SRCALPHA); s.fill(col); screen.blit(s, (0, 0))

def draw_overlays():
    blink = gtime % 70 < 45
    if state == 'title':
        overlay()
        text.text_out(screen, TITLE_BIG, WW//2, 165, 76, '#ffd23f', True)
        text.text_out(screen, TITLE_SUB, WW//2, 215, 32, '#8fd3ff', True)
        text.text_out(screen, TITLE_HINT_1, WW//2, 300, 24, '#cfc8e8', True)
        text.text_out(screen, TITLE_HINT_2, WW//2, 332, 24, '#cfc8e8', True)
        text.text_out(screen, TITLE_HINT_3, WW//2, 380, 22, '#9a90b8', True)
        if blink: text.text_out(screen, TITLE_PROMPT, WW//2, 450, 36, '#ffd23f', True)
    elif state == 'pause':
        overlay()
        text.text_out(screen, PAUSE_TITLE, WW//2, 270, 60, '#8fd3ff', True)
    elif state == 'gameover':
        overlay((30, 5, 10, 180))
        text.text_out(screen, "GAME OVER", WW//2, 235, 68, '#e23b4e', True)
        if blink: text.text_out(screen, "Нажми R для рестарта", WW//2, 320, 28, '#fff', True)
    elif state == 'win':
        overlay((5, 15, 10, 170))
        text.text_out(screen, "YOU WIN!", WW//2, 205, 66, '#7fff8a', True)
        text.text_out(screen, "Уровень пройден", WW//2, 258, 28, '#cfc8e8', True)
        if blink: text.text_out(screen, "Нажми R для рестарта", WW//2, 350, 28, '#fff', True)

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
        render()
        pygame.display.flip()
    pygame.quit()

if __name__ == '__main__':
    main()