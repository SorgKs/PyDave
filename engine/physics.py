# engine/physics.py — универсальная физика с двухпроходной обработкой коллизий
"""
Ответственность:
- Применение гравитации и трения
- Коллизии со статикой (surface_map)
- Межобъектные коллизии (с использованием spatial grid + фильтров)
- Запись детальной информации о коллизиях

Работает в два прохода:
1. Индивидуальная физика + коллизии со статикой + регистрация межобъектных пересечений
2. Разрешение межобъектных коллизий (отталкивание)

После физики в obj['collisions'] записываются:
- target: объект или None (для статики)
- normal: нормаль (nx, ny)
- depth: глубина проникновения
- point: точка контакта (px, py)
"""

import pygame
from engine import objects

# ============================================================================
# ГЛОБАЛЬНЫЕ ДАННЫЕ
# ============================================================================

_TS = 40  # размер тайла (будет установлен из init)
_surface_grid = None  # карта поверхности (0=пусто, 1=стена, 2=платформа)
_ROWS = 0
_COLS = 0

# Пространственная сетка для межобъектных коллизий
_spatial_grid = {}
_CELL_SIZE = 64  # размер ячейки spatial grid


# ============================================================================
# ИНИЦИАЛИЗАЦИЯ
# ============================================================================

def init_physics(ts, surface_grid, rows, cols):
    """
    Инициализирует физику с параметрами уровня.
    
    Args:
        ts: размер тайла в пикселях
        surface_grid: 2D массив карты поверхности (0=пусто, 1=стена, 2=платформа)
        rows: количество рядов
        cols: количество колонок
    """
    global _TS, _surface_grid, _ROWS, _COLS
    _TS = ts
    _surface_grid = surface_grid
    _ROWS = rows
    _COLS = cols


# ============================================================================
# ПРОВЕРКА СТАТИКИ
# ============================================================================

def tile_at(tx, ty):
    """
    Проверяет тип тайла по координатам сетки.
    
    Returns:
        0: пусто
        1: непроходимый (стена/пол)
        2: платформа (можно запрыгнуть снизу)
    """
    if tx < 0 or tx >= _COLS:
        return 1  # границы по X — стены
    if ty < 0:
        return 1  # потолок — стена
    if ty >= _ROWS:
        return 0  # ниже уровня — пусто
    return _surface_grid[ty][tx]


def is_solid_point(x, y):
    """Проверяет, является ли точка твердой (тайл = 1)."""
    return tile_at(int(x // _TS), int(y // _TS)) == 1


def is_platform_point(x, y):
    """Проверяет, является ли точка платформой (тайл = 2)."""
    ty = int(y // _TS)
    if 0 <= ty < _ROWS:
        return _surface_grid[ty][int(x // _TS)] == 2
    return False


# ============================================================================
# ФИЗИКА ОБЪЕКТА (PASS 1)
# ============================================================================

def apply_gravity(obj):
    """Применяет гравитацию к объекту."""
    obj['vy'] += objects.GRAVITY
    if obj['vy'] > objects.MAX_FALL_SPEED:
        obj['vy'] = objects.MAX_FALL_SPEED


def apply_friction(obj):
    """Применяет трение к горизонтальной скорости."""
    friction = objects.FRICTION_GROUND if obj['onG'] else objects.FRICTION_AIR
    obj['vx'] *= friction
    if abs(obj['vx']) < objects.MIN_SPEED:
        obj['vx'] = 0.0


def check_static_collision(obj, prev_bottom_y):
    """
    Проверяет и разрешает коллизии объекта со статикой (стены, пол, платформы).
    
    Записывает коллизии в obj['collisions'].
    
    Args:
        obj: объект
        prev_bottom_y: предыдущая Y-координата низа объекта (для проверки платформ)
    
    Returns:
        bool: True если были коллизии со статикой
    """
    collided = False
    
    # Применяем вертикальную скорость
    obj['y'] += obj['vy']
    obj['onG'] = False
    
    # Вычисляем границы хитбокса
    hx = obj['x'] + obj['hitbox_offset_x']
    hy = obj['y'] + obj['hitbox_offset_y']
    hw, hh = obj['w'], obj['h']
    
    # === ПРОВЕРКА ПОЛА И ПЛАТФОРМ ===
    bottom_y = hy + hh
    ty = int(bottom_y // _TS)
    
    # Проверяем тайлы под хитбоксом
    start_tx = int(hx // _TS)
    end_tx = int((hx + hw - 0.1) // _TS) + 1
    
    land_y = None
    
    for tx in range(start_tx, end_tx):
        tile_type = tile_at(tx, ty)
        
        if tile_type == 1:  # Твердый пол/стена
            land_y = ty * _TS
            break
            
        elif tile_type == 2:  # Платформа
            # Можно приземлиться только если падаем вниз и ранее были выше платформы
            platform_y = ty * _TS
            if obj['vy'] >= 0 and prev_bottom_y <= platform_y + 0.5:
                land_y = platform_y
                break
    
    if land_y is not None and obj['vy'] >= 0:
        # Приземление
        offset_adjustment = obj['hitbox_offset_y'] + hh
        obj['y'] = land_y - offset_adjustment
        obj['vy'] = 0.0
        obj['onG'] = True
        
        # Записываем коллизию со статикой
        objects.add_collision(
            obj,
            target=None,
            normal=(0.0, -1.0),
            depth=bottom_y - land_y,
            point=(obj['x'], bottom_y),
            collision_type='static'
        )
        collided = True
    
    # === ПРОВЕРКА ПОТОЛКА ===
    if obj['vy'] < 0:
        top_y = hy
        ty = int(top_y // _TS)
        
        for tx in range(start_tx, end_tx):
            if tile_at(tx, ty) == 1:
                ceiling_y = (ty + 1) * _TS
                obj['y'] = ceiling_y - obj['hitbox_offset_y'] + 0.01
                obj['vy'] = 0.0
                
                objects.add_collision(
                    obj,
                    target=None,
                    normal=(0.0, 1.0),
                    depth=ceiling_y - top_y,
                    point=(obj['x'], top_y),
                    collision_type='static'
                )
                collided = True
                break
    
    # === ПРОВЕРКА СТЕН (горизонтальные коллизии) ===
    obj['x'] += obj['vx']
    hx = obj['x'] + obj['hitbox_offset_x']
    
    if obj['vx'] > 0:  # Движение вправо
        right_x = hx + hw
        tx = int(right_x // _TS)
        
        # Проверяем несколько точек по высоте
        for check_y_offset in [1, hh // 2, hh - 1]:
            check_y = hy + check_y_offset
            if is_solid_point(right_x, check_y):
                wall_x = tx * _TS
                obj['x'] = wall_x - obj['hitbox_offset_x'] - hw - 0.01
                obj['vx'] = 0.0
                
                objects.add_collision(
                    obj,
                    target=None,
                    normal=(-1.0, 0.0),
                    depth=right_x - wall_x,
                    point=(right_x, obj['y'] + check_y_offset),
                    collision_type='static'
                )
                collided = True
                break
                
    elif obj['vx'] < 0:  # Движение влево
        left_x = hx
        tx = int(left_x // _TS)
        
        for check_y_offset in [1, hh // 2, hh - 1]:
            check_y = hy + check_y_offset
            if is_solid_point(left_x, check_y):
                wall_x = (tx + 1) * _TS
                obj['x'] = wall_x - obj['hitbox_offset_x'] + 0.01
                obj['vx'] = 0.0
                
                objects.add_collision(
                    obj,
                    target=None,
                    normal=(1.0, 0.0),
                    depth=wall_x - left_x,
                    point=(left_x, obj['y'] + check_y_offset),
                    collision_type='static'
                )
                collided = True
                break
    
    return collided


# ============================================================================
# ПРОСТРАНСТВЕННАЯ СЕТКА (SPATIAL GRID)
# ============================================================================

def _build_spatial_grid(objects_list):
    """
    Строит пространственную сетку для быстрого поиска пар коллизий.
    
    Args:
        objects_list: список объектов для проверки
    """
    global _spatial_grid
    _spatial_grid = {}
    
    for obj in objects_list:
        # Определяем, какие объекты участвуют в межобъектных коллизиях
        layer = obj.get('layer', objects.LAYER_NONE)
        if layer == objects.LAYER_NONE:
            continue
        
        # Проверяем, есть ли у этого слоя потенциальные цели для коллизий
        can_collide = False
        for other_layer, mask in objects.COLLISION_MATRIX.items():
            if layer & mask:
                can_collide = True
                break
        
        if not can_collide:
            continue
        
        # Добавляем объект в ячейки сетки
        hx = obj['x'] + obj['hitbox_offset_x']
        hy = obj['y'] + obj['hitbox_offset_y']
        hw, hh = obj['w'], obj['h']
        
        start_cx = int(hx // _CELL_SIZE)
        end_cx = int((hx + hw) // _CELL_SIZE)
        start_cy = int(hy // _CELL_SIZE)
        end_cy = int((hy + hh) // _CELL_SIZE)
        
        for cx in range(start_cx, end_cx + 1):
            for cy in range(start_cy, end_cy + 1):
                cell_key = (cx, cy)
                if cell_key not in _spatial_grid:
                    _spatial_grid[cell_key] = []
                _spatial_grid[cell_key].append(obj)


def _get_nearby_objects(obj):
    """
    Возвращает список объектов, которые могут столкнуться с данным.
    
    Использует пространственную сетку и фильтры слоев.
    """
    nearby = set()
    
    hx = obj['x'] + obj['hitbox_offset_x']
    hy = obj['y'] + obj['hitbox_offset_y']
    hw, hh = obj['w'], obj['h']
    
    start_cx = int(hx // _CELL_SIZE)
    end_cx = int((hx + hw) // _CELL_SIZE)
    start_cy = int(hy // _CELL_SIZE)
    end_cy = int((hy + hh) // _CELL_SIZE)
    
    my_layer = obj.get('layer', objects.LAYER_NONE)
    collision_mask = objects.COLLISION_MATRIX.get(my_layer, 0)
    
    for cx in range(start_cx, end_cx + 1):
        for cy in range(start_cy, end_cy + 1):
            cell_key = (cx, cy)
            if cell_key in _spatial_grid:
                for other in _spatial_grid[cell_key]:
                    if other is obj:
                        continue
                    other_layer = other.get('layer', objects.LAYER_NONE)
                    # Проверяем фильтр коллизий
                    if my_layer & other_layer:
                        continue
                    if (my_layer & collision_mask) and (other_layer & collision_mask):
                        nearby.add(other)
    
    return list(nearby)


# ============================================================================
# МЕЖОБЪЕКТНЫЕ КОЛЛИЗИИ (PASS 2)
# ============================================================================

def resolve_object_collisions(objects_list):
    """
    Разрешает межобъектные коллизии с отталкиванием.
    
    Вызывается после PASS 1 для всех объектов.
    Записывает коллизии в obj['collisions'].
    
    Args:
        objects_list: список всех объектов
    """
    # Строим пространственную сетку
    _build_spatial_grid(objects_list)
    
    processed_pairs = set()
    
    for obj in objects_list:
        my_layer = obj.get('layer', objects.LAYER_NONE)
        if my_layer == objects.LAYER_NONE:
            continue
        
        nearby = _get_nearby_objects(obj)
        
        for other in nearby:
            # Избегаем двойной обработки пар
            pair_id = tuple(sorted([id(obj), id(other)]))
            if pair_id in processed_pairs:
                continue
            processed_pairs.add(pair_id)
            
            other_layer = other.get('layer', objects.LAYER_NONE)
            
            # Проверяем матрицу коллизий
            my_mask = objects.COLLISION_MATRIX.get(my_layer, 0)
            other_mask = objects.COLLISION_MATRIX.get(other_layer, 0)
            
            if not ((my_layer & other_mask) or (other_layer & my_mask)):
                continue
            
            # Проверяем пересечение хитбоксов
            rect1 = objects.get_hitbox_rect(obj)
            rect2 = objects.get_hitbox_rect(other)
            
            if not rect1.colliderect(rect2):
                continue
            
            # Вычисляем глубину и направление коллизии
            dx = (obj['x'] + obj['hitbox_offset_x'] + obj['w'] / 2) - \
                 (other['x'] + other['hitbox_offset_x'] + other['w'] / 2)
            dy = (obj['y'] + obj['hitbox_offset_y'] + obj['h'] / 2) - \
                 (other['y'] + other['hitbox_offset_y'] + other['h'] / 2)
            
            overlap_x = (obj['w'] + other['w']) / 2 - abs(dx)
            overlap_y = (obj['h'] + other['h']) / 2 - abs(dy)
            
            if overlap_x <= 0 or overlap_y <= 0:
                continue
            
            # Определяем направление наименьшего проникновения
            if overlap_x < overlap_y:
                # Горизонтальное разрешение
                depth = overlap_x
                normal_x = 1.0 if dx > 0 else -1.0
                normal_y = 0.0
                
                obj['x'] += normal_x * depth * 0.5
                other['x'] -= normal_x * depth * 0.5
                
                # Отскок по горизонтали
                if obj['vx'] * normal_x > 0:
                    obj['vx'] *= -0.3
                if other['vx'] * (-normal_x) > 0:
                    other['vx'] *= -0.3
                    
            else:
                # Вертикальное разрешение
                depth = overlap_y
                normal_x = 0.0
                normal_y = 1.0 if dy > 0 else -1.0
                
                obj['y'] += normal_y * depth * 0.5
                other['y'] -= normal_y * depth * 0.5
                
                # Отскок по вертикали
                if obj['vy'] * normal_y > 0:
                    obj['vy'] *= -0.3
                if other['vy'] * (-normal_y) > 0:
                    other['vy'] *= -0.3
            
            # Точка контакта
            contact_x = (rect1.centerx + rect2.centerx) / 2
            contact_y = (rect1.centery + rect2.centery) / 2
            
            # Записываем коллизии для обоих объектов
            objects.add_collision(
                obj,
                target=other,
                normal=(normal_x, normal_y),
                depth=depth,
                point=(contact_x, contact_y),
                collision_type='object'
            )
            
            objects.add_collision(
                other,
                target=obj,
                normal=(-normal_x, -normal_y),
                depth=depth,
                point=(contact_x, contact_y),
                collision_type='object'
            )


# ============================================================================
# ГЛАВНЫЙ ЦИКЛ ФИЗИКИ
# ============================================================================

def update_physics(objects_list):
    """
    Полный цикл физики (2 прохода).
    
    Args:
        objects_list: список всех объектов
    """
    # Очищаем старые коллизии
    objects.clear_collisions(objects_list)
    
    # === PASS 1: Индивидуальная физика + коллизии со статикой ===
    for obj in objects_list:
        prev_bottom_y = obj['y'] + obj['hitbox_offset_y'] + obj['h']
        
        # Применяем гравитацию (если объект не летающий без гравитации)
        if obj.get('has_gravity', True):
            apply_gravity(obj)
        
        # Сохраняем onG до движения
        was_on_ground = obj['onG']
        
        # Разрешаем коллизии со статикой
        check_static_collision(obj, prev_bottom_y)
        
        # Применяем трение
        apply_friction(obj)
    
    # === PASS 2: Межобъектные коллизии ===
    resolve_object_collisions(objects_list)
