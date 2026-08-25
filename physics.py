# physics.py — физика игры
import math

# Глобальные переменные для физики (будут установлены из main.py)
_TS = 40
_surface_grid = None
_ROWS = 0
_COLS = 0

# Параметры физики
GRAVITY = 0.4
MAX_FALL_SPEED = 10
JUMP_SPEED = -5.5
FRICTION = 0.8
MIN_SPEED = 0.1

def init_physics(ts, surface_grid, rows, cols):
    """Инициализирует физику с параметрами уровня"""
    global _TS, _surface_grid, _ROWS, _COLS
    _TS = ts
    _surface_grid = surface_grid
    _ROWS = rows
    _COLS = cols

def tile_at(tx, ty):
    """Проверяет тайл по координатам"""
    if tx < 0 or tx >= _COLS: return 1
    if ty < 0: return 1
    if ty >= _ROWS: return 0
    return _surface_grid[ty][tx]

def solid_pt(x, y):
    """Проверяет, является ли точка твердой"""
    return tile_at(int(x // _TS), int(y // _TS)) == 1

def move_x(e):
    """Горизонтальное движение с коллизией"""
    e['x'] += e['vx']
    e['hitW'] = False
    
    def is_solid(x, y):
        return solid_pt(x, y)
    
    if e['vx'] > 0:
        r = e['x'] + e['w']
        if is_solid(r, e['y']+1) or is_solid(r, e['y']+e['h']/2) or is_solid(r, e['y']+e['h']-1):
            e['x'] = int(r // _TS)*_TS - e['w'] - .01
            e['vx'] = 0
            e['hitW'] = True
    elif e['vx'] < 0:
        if is_solid(e['x'], e['y']+1) or is_solid(e['x'], e['y']+e['h']/2) or is_solid(e['x'], e['y']+e['h']-1):
            e['x'] = (int(e['x'] // _TS) + 1)*_TS + .01
            e['vx'] = 0
            e['hitW'] = True

def move_y(e, prev_bottom):
    """
    Вертикальное движение с коллизией.
    На каждом такте считаем новое положение по y как если бы падал.
    Если оказываемся внутри пола или платформы - изменяем y вровень с полом/платформой и выставляем onG.
    """
    # Применяем вертикальную скорость
    e['y'] += e['vy']
    
    # Всегда сбрасываем onG в начале
    e['onG'] = False
    
    # Определяем нижнюю точку хитбокса с учетом оффсета спрайта
    sprite_h = e.get('sprite_h', e['h'])
    offset = (e['sprite_h'] - e['h']) / 2
    bot = e['y'] + e['h'] + offset
    
    # Проверяем, есть ли тайл под ногами на любой скорости (включая vy=0)
    ty = int(bot // _TS)
    land = -1
    found_platform = False
    
    # Проходим по всем тайлам под хитбоксом
    for tx in range(int(e['x'] // _TS), int((e['x'] + e['w'] - 0.1) // _TS) + 1):
        # Проверка на твердый пол (значение 1)
        if tile_at(tx, ty) == 1:
            land = ty * _TS
            found_platform = True
            break
        # Проверка на платформу (значение 2)
        if 0 <= ty < _ROWS and _surface_grid[ty][tx] == 2:
            # Проверяем, что игрок падает на платформу или стоит на ней
            if prev_bottom <= ty * _TS + 0.5 and e.get('drop', 0) <= 0:
                land = ty * _TS
                found_platform = True
                break
    
    # Если нашли опору
    if found_platform and land >= 0:
        # Если игрок внутри пола (или касается его), приземляем
        if e['vy'] >= 0:
            e['y'] = land - e['h'] - offset
            e['vy'] = 0
            e['onG'] = True
    else:
        # Если игрок улетел слишком далеко вниз, считаем что он упал
        if e['y'] > _ROWS * _TS + 100:
            pass
    
    # Проверка на столкновение с потолком (только при прыжке вверх)
    if e['vy'] < 0:
        ty = int(e['y'] // _TS)
        for tx in range(int(e['x'] // _TS), int((e['x'] + e['w'] - 0.1) // _TS) + 1):
            if tile_at(tx, ty) == 1:
                e['y'] = (ty + 1) * _TS + 0.01
                e['vy'] = 0
                break

def update_player_physics(p):
    """Обновляет физику игрока"""
    prev_bottom = p['y'] + p['h']
    
    # Применяем гравитацию
    p['vy'] += GRAVITY
    if p['vy'] > MAX_FALL_SPEED:
        p['vy'] = MAX_FALL_SPEED
    
    # Горизонтальное движение
    move_x(p)
    
    # Вертикальное движение (проверяет землю на каждом такте)
    move_y(p, prev_bottom)
    
    # Применяем трение к горизонтальной скорости
    p['vx'] *= FRICTION
    if abs(p['vx']) < MIN_SPEED:
        p['vx'] = 0
    
    # Центрирование хитбокса внутри спрайта
    offset_x = (p['sprite_w'] - p['w']) // 2
    offset_y = (p['sprite_h'] - p['h']) // 2
    p['sx'] = p['x'] - offset_x
    p['sy'] = p['y'] - offset_y

def jump(p):
    """Выполняет прыжок"""
    if p['onG'] and p.get('drop', 0) <= 0:
        p['vy'] = JUMP_SPEED
        p['jbuf'] = 0
        return True
    return False

def rect_collide(r1, r2):
    """Проверяет столкновение двух прямоугольников"""
    return (r1.x < r2.x + r2.w and r1.x + r1.w > r2.x and
            r1.y < r2.y + r2.h and r1.y + r1.h > r2.y)

def p_rect(p):
    """Возвращает прямоугольник хитбокса объекта"""
    return type('Rect', (), {
        'x': int(p['x']),
        'y': int(p['y']),
        'w': p['w'],
        'h': p['h']
    })()

def p_rect_pygame(p):
    """Возвращает pygame.Rect объекта"""
    import pygame
    return pygame.Rect(int(p['x']), int(p['y']), p['w'], p['h'])

def distance(p1, p2):
    """Расстояние между двумя точками"""
    return math.sqrt((p1['x'] - p2['x'])**2 + (p1['y'] - p2['y'])**2)

def apply_gravity(e, gravity=GRAVITY):
    """Применяет гравитацию к объекту"""
    e['vy'] += gravity
    if e['vy'] > MAX_FALL_SPEED:
        e['vy'] = MAX_FALL_SPEED

def apply_friction(e, friction=FRICTION, min_speed=MIN_SPEED):
    """Применяет трение к объекту"""
    e['vx'] *= friction
    if abs(e['vx']) < min_speed:
        e['vx'] = 0