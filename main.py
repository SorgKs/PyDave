#!/usr/bin/env python3
# main.py — DAVE DANGEROUS: Haunted Mansion (НОВАЯ АРХИТЕКТУРА)
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
import tilemap
from tiles import load_tiles
from surface_map import build_surface_map

# НОВЫЕ МОДУЛИ
from engine import physics, render, objects
from anims import dave, zombie, goblin, ghost, skull  # Загружаем модули объектов
from anims import TYPE_TO_MOD, create_object

# Инициализация шрифтов
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
# ЗАГРУЗКА АССЕТОВ
# ============================================================================

I = load_all_sprites()

# Загрузка тайлов
TILES = load_tiles()
I.update(TILES)

def have(n):
    return n in I

WHITE = {n: make_white_variant(I[n]) for n in I if n.startswith(('zombie', 'ghost', 'bat'))}

SFX, MUSIC = (load_all_sounds() if AUDIO else ({}, None))
MUTED = [False]

def play(n):
    if AUDIO and not MUTED[0] and SFX.get(n):
        SFX[n].play()

# ============================================================================
# ИНИЦИАЛИЗАЦИЯ УРОВНЯ
# ============================================================================

# Визуальная карта
tilemap.init_tilemap()

# Физическая карта (surface_map)
surface_grid, ROWS, COLS = build_surface_map(verbose=False)
physics.init_physics(TS, surface_grid, ROWS, COLS)

# Парсинг объектов из уровня
data = levels.parse_objects(lvl.MAP)
spikes = data['spikes']
torches = data['torches']
gems = data['gems']
hearts = data['hearts']
skulls_list = data['skulls']  # Переименовано для избежания конфликта
enemies_data = data['enemies']
door = data['door']
key_pos = data['key_pos']
doors_decor = data['doors_decor']
spawn_pos = data['spawn_pos']

# ============================================================================
# СОЗДАНИЕ ОБЪЕКТОВ
# ============================================================================

# Список всех объектов
all_objects = []

# Создаем игрока
player_obj = create_object('dave', spawn_pos[0], spawn_pos[1])
player_obj.compute_offsets()
all_objects.append(player_obj)

# Создаем врагов
for enemy in enemies_data:
    enemy_type = enemy.get('type', 'zombie')
    ex = enemy.get('x', 0)
    ey = enemy.get('y', 0)
    params = enemy.get('params', {})
    
    enemy_obj = create_object(enemy_type, ex, ey, params)
    enemy_obj.compute_offsets()
    all_objects.append(enemy_obj)

# Создаем предметы (gems)
for gem in gems:
    if not gem.get('taken', False):
        gem_obj = create_object('item_gem', gem['x'], gem['y'])
        gem_obj.compute_offsets()
        all_objects.append(gem_obj)

# Камера и состояние
cam_x = cam_y = 0.0
shake = 0.0
state, state_t, gtime = 'title', 0, 0
parts, texts = [], []
view = pygame.Surface((VW, VH))

ENEMY_DRAW_OFF = {'z': (-4, -4), 'g': (-2, -1), 'b': (-2, -2)}

# ============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================================

def reset_game():
    """Сброс игры к начальному состоянию."""
    global state, state_t, all_objects, player_obj
    
    # Очищаем объекты
    all_objects.clear()
    
    # Пересоздаем игрока
    player_obj = create_object('dave', spawn_pos[0], spawn_pos[1])
    player_obj.compute_offsets()
    all_objects.append(player_obj)
    
    # Пересоздаем врагов
    enemies_data = levels.parse_objects(lvl.MAP)['enemies']
    for enemy in enemies_data:
        enemy_type = enemy.get('type', 'zombie')
        ex = enemy.get('x', 0)
        ey = enemy.get('y', 0)
        params = enemy.get('params', {})
        
        enemy_obj = create_object(enemy_type, ex, ey, params)
        enemy_obj.compute_offsets()
        all_objects.append(enemy_obj)
    
    # Сброс предметов
    for g in gems:
        g['taken'] = False
    for h in hearts:
        h['taken'] = False
    if door is not None:
        door['open'] = 0.0
    
    parts.clear()
    texts.clear()
    
    state = 'play'
    state_t = 0

def add_parts(x, y, n, col, spd, g=.08):
    """Добавляет частицы."""
    for _ in range(n):
        a = random.random()*6.2832
        v = (.3 + random.random())*spd
        parts.append({
            'x': x, 'y': y,
            'vx': math.cos(a)*v,
            'vy': math.sin(a)*v - 1,
            'g': g,
            'life': 0,
            'max': 25 + random.random()*20,
            'col': col,
            'sz': 1 + random.random()*2
        })

def add_text(x, y, t, col='#fff'):
    """Добавляет всплывающий текст."""
    texts.append({'x': x, 'y': y, 'txt': t, 'col': col, 'life': 0})

def shake_amt(v):
    """Устанавливает тряску камеры."""
    global shake
    shake = max(shake, v)

def kill_player():
    """Убивает игрока."""
    global state, state_t
    if state != 'play':
        return
    play('die')
    shake_amt(9)
    add_parts(player_obj.x, player_obj.y, 26, '#e23b4e', 3)
    state = 'gameover'
    state_t = 0

def hurt_player(src_x):
    """Наносит урон игроку."""
    if player_obj.inv > 0 or state != 'play':
        return
    player_obj.inv = 85
    play('hurt')
    shake_amt(5)
    add_parts(player_obj.x, player_obj.y, 10, '#e23b4e', 2)
    player_obj.vx = -3 if player_obj.x < src_x else 3
    player_obj.vy = -3.5
    kill_player()

# Контекст для обратной совместимости
class _Ctx:
    pass

CTX = _Ctx()
CTX.TS, CTX.ROWS, CTX.COLS, CTX.grid = TS, ROWS, COLS, surface_grid
CTX.spikes = spikes
CTX.play, CTX.add_parts, CTX.shake = play, add_parts, shake_amt
CTX.hurt, CTX.kill = hurt_player, kill_player

# ============================================================================
# UPDATE
# ============================================================================

def update(pressed, held):
    """Обновление игровой логики."""
    global state, state_t, gtime, cam_x, cam_y, shake
    
    gtime += 1
    state_t += 1
    
    # Обработка клавиш
    if pygame.K_m in pressed:
        MUTED[0] = not MUTED[0]
        if AUDIO and MUSIC:
            MUSIC.set_volume(0 if MUTED[0] else MUSIC_VOL)
    
    if pygame.K_r in pressed and state in ('play', 'gameover', 'win'):
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
    elif state in ('gameover', 'win'):
        if pygame.K_RETURN in pressed:
            reset_game()
    elif state == 'play':
        # === ШАГ 1: BEHAVE (логика поведения) ===
        input_state = {'pressed': pressed, 'held': held}
        
        for obj in all_objects:
            obj.t += 1
            if hasattr(obj, 'flash') and obj.flash > 0:
                obj.flash -= 1
            
            # Вызываем behave для каждого объекта
            obj.behave(input_state, CTX)
        
        # === ШАГ 2: PHYSICS (2 прохода) ===
        physics.update_physics(all_objects)
        
        # === ШАГ 3: TRANSFORM (реакция на коллизии) ===
        for obj in all_objects:
            if obj.collisions:
                obj.transform()
        
        # Проверка победы (дверь)
        if door is not None:
            player_rect = objects.get_hitbox_rect(player_obj)
            door_rect = pygame.Rect(door['x'] + 2, door['y'] + 6, 12, 26)
            if player_rect.colliderect(door_rect):
                if door['open'] >= 1 and state_t > 30:
                    state = 'win'
                    state_t = 0
        
        # Проверка коллизий игрока с врагами (для урона)
        if state == 'play' and player_obj.inv <= 0:
            for enemy in all_objects:
                if hasattr(enemy, 'layer') and enemy.layer == objects.LAYER_ENEMY:
                    enemy_rect = objects.get_hitbox_rect(enemy)
                    if player_rect.colliderect(enemy_rect):
                        hurt_player(enemy.x + enemy.w / 2)
    
    # Обновление частиц
    for p in parts[:]:
        p['x'] += p['vx']
        p['y'] += p['vy']
        p['vy'] += p['g']
        p['life'] += 1
        if p['life'] > p['max']:
            parts.remove(p)
    
    # Обновление текста
    for t in texts[:]:
        t['y'] -= .4
        t['life'] += 1
        if t['life'] > 60:
            texts.remove(t)
    
    # Тряска камеры
    shake *= .86
    if shake < .2:
        shake = 0
    
    # Открытие двери
    if door is not None and 0 < door['open'] < 1:
        door['open'] = min(1.0, door['open'] + .04)
    
    # Камера следует за игроком
    if state == 'title':
        tx = 40 + (math.sin(gtime*.004)*.5 + .5)*(COLS*TS - VW - 80)
        ty = 32 + math.sin(gtime*.002)*20
    else:
        # Позиция спрайта игрока для камеры
        sprite_x = player_obj.x + player_obj.sprite_offset_x
        sprite_y = player_obj.y + player_obj.sprite_offset_y
        tx = sprite_x + player_obj.sprite_w//2 - VW/2 + player_obj.face*28
        ty = sprite_y + player_obj.sprite_h//2 - VH/2
    
    cam_x += (tx - cam_x)*.1
    cam_y += (ty - cam_y)*.12
    cam_x = max(0, min(cam_x, COLS*TS - VW))
    cam_y = max(0, min(cam_y, ROWS*TS - VH))

# ============================================================================
# RENDER
# ============================================================================

def blit(surf, im, x, y, flip=False, alpha=None):
    """Отрисовка изображения с опциями."""
    if flip:
        im = pygame.transform.flip(im, True, False)
    if alpha is not None:
        im.set_alpha(alpha)
    surf.blit(im, (int(round(x)), int(round(y))))

def render():
    """Отрисовка кадра."""
    view.fill((0, 0, 0))
    ox = int(cam_x + (random.random() - .5)*shake)
    oy = int(cam_y + (random.random() - .5)*shake)
    
    # === ОТРИСОВКА ТАЙЛОВ ===
    x0 = max(0, ox // TS)
    x1 = min(tilemap.cols - 1, (ox + VW) // TS + 1)
    y0 = max(0, oy // TS)
    y1 = min(tilemap.rows - 1, (oy + VH) // TS + 1)
    
    for ty in range(y0, y1 + 1):
        for tx in range(x0, x1 + 1):
            tile_name = tilemap.grid[ty][tx]
            if not tile_name:
                continue
            im = I.get(tile_name)
            if im is None:
                continue
            px = tx * TS - ox
            py = ty * TS - oy
            view.blit(im, (int(round(px)), int(round(py))))
    
    # === СТАТИЧЕСКИЕ ОБЪЕКТЫ ===
    if 'spike' in I:
        for s in spikes:
            if ox - 16 <= s['x'] <= ox + VW + 16:
                view.blit(I['spike'], (s['x'] - ox, s['y'] - oy))
    
    if 'skull' in I:
        for sx, sy in skulls_list:
            view.blit(I['skull'], (sx - ox, sy - oy))
    
    # Факелы
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
    
    # Декор дверей
    for dx, dy in doors_decor:
        if 'door_orig' in I:
            view.blit(I['door_orig'], (dx - ox - 8, dy - oy - 16))
        elif 'door_closed' in I:
            view.blit(I['door_closed'], (dx - ox, dy - oy))
    
    # Дверь выхода
    if door is not None:
        if 'door_orig' in I:
            view.blit(I['door_orig'], (door['x'] - ox - 8, door['y'] - oy - 16))
        else:
            door_name = 'door_open' if door['open'] > 0 else 'door_closed'
            if door_name in I:
                view.blit(I[door_name], (door['x'] - ox, door['y'] - oy))
    
    # Предметы
    if 'gem' in I:
        for g in gems:
            if g['taken']:
                continue
            bob = math.sin(gtime*.08 + g['seed'])*2
            view.blit(I['gem'], (g['x'] - ox, g['y'] - oy + bob))
    
    if 'heart' in I:
        for h in hearts:
            if h['taken']:
                continue
            s = 1 + .08*math.sin(gtime*.15)
            im = pygame.transform.scale(I['heart'], (int(16*s), int(16*s)))
            view.blit(im, (h['x'] - ox - im.get_width()//2 + 8, h['y'] - oy - im.get_height()//2 + 8))
    
    # === ОТРИСОВКА ОБЪЕКТОВ ===
    gh_alpha = int(200 + 40*math.sin(gtime*.1))
    
    for obj in all_objects:
        # Пропускаем игрока (рисуется отдельно)
        if obj is player_obj:
            continue
        
        # Пропускаем вне экрана
        if obj.x < ox - 60 or obj.x > ox + VW + 60:
            continue
        
        # Получаем спрайт
        sprite_name = obj.get_sprite()
        if not sprite_name or sprite_name not in I:
            continue
        
        # Мигание при уроне
        flip = obj.face < 0
        alpha = None
        
        if hasattr(obj, 'flash') and obj.flash > 0:
            if sprite_name in WHITE:
                im = WHITE[sprite_name]
            else:
                im = I[sprite_name]
        else:
            im = I[sprite_name]
        
        # Свечение призраков
        if hasattr(obj, 'NAME') and obj.NAME == 'ghost' and 'glow_ghost' in I:
            alpha = gh_alpha
            view.blit(I['glow_ghost'], (obj.x - ox - 8, obj.y - oy - 8), special_flags=pygame.BLEND_ADD)
        
        # Смещение для отрисовки
        dx, dy = ENEMY_DRAW_OFF.get(getattr(obj, 'NAME', ''), (0, 0))
        render_x = obj.x + obj.sprite_offset_x - ox + dx
        render_y = obj.y + obj.sprite_offset_y - oy + dy
        
        blit(view, im, render_x, render_y, flip, alpha)
    
    # === ОТРИСОВКА ИГРОКА ===
    if state not in ('title', 'gameover'):
        if not (player_obj.inv > 0 and gtime % 6 < 3 and state == 'play'):
            sprite_name = player_obj.get_sprite()
            if sprite_name in I:
                im = I[sprite_name]
                w, h = im.get_width(), im.get_height()
                
                oy2 = -1 if (abs(player_obj.vx) > .3 and player_obj.onG and math.sin(gtime*.4) > .5) else 0
                render_x = player_obj.x + player_obj.sprite_offset_x - ox
                render_y = player_obj.y + player_obj.sprite_offset_y - oy + oy2
                
                blit(view, im, render_x, render_y, player_obj.face < 0)
    
    # === ЧАСТИЦЫ ===
    for p in parts:
        a = max(0, 1 - p['life']/p['max'])
        col = pygame.Color(p['col'])
        col.r = int(col.r*a)
        col.g = int(col.g*a)
        col.b = int(col.b*a)
        pygame.draw.rect(view, col, (p['x'] - ox, p['y'] - oy, p['sz'], p['sz']))
    
    # === МАСШТАБИРОВАНИЕ НА ЭКРАН ===
    pygame.transform.scale(view, (WW, WH), screen)
    
    # === ТЕКСТЫ ===
    if text.FONT_OK:
        for t in texts:
            im = text.font(16).render(t['txt'], True, pygame.Color(t['col']))
            im.set_alpha(int(255*max(0, 1 - t['life']/60)))
            screen.blit(im, ((t['x'] - ox)*SCALE, (t['y'] - oy)*SCALE))
    
    draw_overlays()

def overlay(col=(5, 3, 12, 150)):
    """Полупрозрачное перекрытие."""
    s = pygame.Surface((WW, WH), pygame.SRCALPHA)
    s.fill(col)
    screen.blit(s, (0, 0))

def draw_overlays():
    """Отрисовка интерфейса."""
    blink = gtime % 70 < 45
    
    if state == 'title':
        overlay()
        text.text_out(screen, TITLE_BIG, WW//2, 165, 76, '#ffd23f', True)
        text.text_out(screen, TITLE_SUB, WW//2, 215, 32, '#8fd3ff', True)
        text.text_out(screen, TITLE_HINT_1, WW//2, 300, 24, '#cfc8e8', True)
        text.text_out(screen, TITLE_HINT_2, WW//2, 332, 24, '#cfc8e8', True)
        text.text_out(screen, TITLE_HINT_3, WW//2, 380, 22, '#9a90b8', True)
        if blink:
            text.text_out(screen, TITLE_PROMPT, WW//2, 450, 36, '#ffd23f', True)
    
    elif state == 'pause':
        overlay()
        text.text_out(screen, PAUSE_TITLE, WW//2, 270, 60, '#8fd3ff', True)
    
    elif state == 'gameover':
        overlay((30, 5, 10, 180))
        text.text_out(screen, "GAME OVER", WW//2, 235, 68, '#e23b4e', True)
        if blink:
            text.text_out(screen, "Нажми R для рестарта", WW//2, 320, 28, '#fff', True)
    
    elif state == 'win':
        overlay((5, 15, 10, 170))
        text.text_out(screen, "YOU WIN!", WW//2, 205, 66, '#7fff8a', True)
        text.text_out(screen, "Уровень пройден", WW//2, 258, 28, '#cfc8e8', True)
        if blink:
            text.text_out(screen, "Нажми R для рестарта", WW//2, 350, 28, '#fff', True)

# ============================================================================
# MAIN LOOP
# ============================================================================

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
