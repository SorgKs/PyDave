# engine/physics.py — физика в тайлах, 2 прохода
"""
Pass1: гравитация/трение + статика + запись collisions.
Pass2: межобъектные + отскок где нужно.
Единицы: тайлы. TS для физики не используется.
"""

from engine import objects

_surface_grid = None
_ROWS = 0
_COLS = 0
_spatial_grid = {}
_CELL_SIZE = 4  # тайлы


def init_physics(surface_grid, rows, cols, ts=None):
    """Инициализирует физику. ts игнорируется (совместимость вызова)."""
    global _surface_grid, _ROWS, _COLS
    _surface_grid = surface_grid
    _ROWS = rows
    _COLS = cols


def tile_at(tx, ty):
    """0 пусто, 1 стена/пол, 2 платформа."""
    if tx < 0 or tx >= _COLS:
        return 1
    if ty < 0:
        return 1
    if ty >= _ROWS:
        return 0
    return _surface_grid[ty][tx]


def is_solid_point(x, y):
    """Точка в тайловых координатах — твёрдый тайл (1)."""
    return tile_at(int(x), int(y)) == 1


def apply_gravity(obj):
    obj['vy'] += objects.GRAVITY
    if obj['vy'] > objects.MAX_FALL_SPEED:
        obj['vy'] = objects.MAX_FALL_SPEED


def apply_friction(obj):
    friction = objects.FRICTION_GROUND if obj['onG'] else objects.FRICTION_AIR
    obj['vx'] *= friction
    if abs(obj['vx']) < objects.MIN_SPEED:
        obj['vx'] = 0.0


def check_static_collision(obj, prev_bottom_y):
    """Разрешает коллизии со статикой; пишет collisions. Координаты в тайлах."""
    collided = False
    obj['hitW'] = False

    obj['y'] += obj['vy']
    obj['onG'] = False

    hx = obj['x'] + obj['hitbox_offset_x']
    hy = obj['y'] + obj['hitbox_offset_y']
    hw, hh = obj['w'], obj['h']

    bottom_y = hy + hh
    ty = int(bottom_y)
    start_tx = int(hx)
    end_tx = int(hx + hw - 1e-6) + 1

    land_y = None
    for tx in range(start_tx, end_tx):
        tile_type = tile_at(tx, ty)
        if tile_type == 1:
            land_y = float(ty)
            break
        if tile_type == 2:
            platform_y = float(ty)
            if obj['vy'] >= 0 and prev_bottom_y <= platform_y + 0.05:
                land_y = platform_y
                break

    if land_y is not None and obj['vy'] >= 0:
        offset_adjustment = obj['hitbox_offset_y'] + hh
        obj['y'] = land_y - offset_adjustment
        obj['vy'] = 0.0
        obj['onG'] = True
        objects.add_collision(obj, 'floor')
        collided = True

    # Потолок
    hy = obj['y'] + obj['hitbox_offset_y']
    if obj['vy'] < 0:
        top_y = hy
        ty = int(top_y)
        for tx in range(start_tx, end_tx):
            if tile_at(tx, ty) == 1:
                ceiling_y = float(ty + 1)
                obj['y'] = ceiling_y - obj['hitbox_offset_y'] + 0.001
                obj['vy'] = 0.0
                objects.add_collision(obj, 'ceiling')
                collided = True
                break

    # Стены
    obj['x'] += obj['vx']
    hx = obj['x'] + obj['hitbox_offset_x']
    hy = obj['y'] + obj['hitbox_offset_y']

    if obj['vx'] > 0:
        right_x = hx + hw
        tx = int(right_x)
        for check_y_offset in (0.05, hh * 0.5, hh - 0.05):
            if is_solid_point(right_x, hy + check_y_offset):
                wall_x = float(tx)
                obj['x'] = wall_x - obj['hitbox_offset_x'] - hw - 0.001
                obj['vx'] = 0.0
                obj['hitW'] = True
                objects.add_collision(obj, 'wall', side='right')
                collided = True
                break
    elif obj['vx'] < 0:
        left_x = hx
        tx = int(left_x)
        for check_y_offset in (0.05, hh * 0.5, hh - 0.05):
            if is_solid_point(left_x, hy + check_y_offset):
                wall_x = float(tx + 1)
                obj['x'] = wall_x - obj['hitbox_offset_x'] + 0.001
                obj['vx'] = 0.0
                obj['hitW'] = True
                objects.add_collision(obj, 'wall', side='left')
                collided = True
                break

    return collided


def _layer_in_collisions(layer):
    """Участвует ли слой в детекции (как источник или цель)."""
    if layer == objects.LAYER_NONE:
        return False
    if objects.COLLISION_MATRIX.get(layer):
        return True
    for targets in objects.COLLISION_MATRIX.values():
        if layer in targets:
            return True
    return False


def _build_spatial_grid(objects_list):
    global _spatial_grid
    _spatial_grid = {}
    for obj in objects_list:
        layer = obj.get('layer', objects.LAYER_NONE)
        if not _layer_in_collisions(layer):
            continue
        hx = obj['x'] + obj['hitbox_offset_x']
        hy = obj['y'] + obj['hitbox_offset_y']
        hw, hh = obj['w'], obj['h']
        for cx in range(int(hx // _CELL_SIZE), int((hx + hw) // _CELL_SIZE) + 1):
            for cy in range(int(hy // _CELL_SIZE), int((hy + hh) // _CELL_SIZE) + 1):
                _spatial_grid.setdefault((cx, cy), []).append(obj)


def _get_nearby_objects(obj):
    nearby = {}
    hx = obj['x'] + obj['hitbox_offset_x']
    hy = obj['y'] + obj['hitbox_offset_y']
    hw, hh = obj['w'], obj['h']
    my_layer = obj.get('layer', objects.LAYER_NONE)

    for cx in range(int(hx // _CELL_SIZE), int((hx + hw) // _CELL_SIZE) + 1):
        for cy in range(int(hy // _CELL_SIZE), int((hy + hh) // _CELL_SIZE) + 1):
            for other in _spatial_grid.get((cx, cy), []):
                if other is obj:
                    continue
                if objects.layers_collide(my_layer, other.get('layer', objects.LAYER_NONE)):
                    nearby[id(other)] = other
    return list(nearby.values())


def _hitboxes_overlap(a, b):
    ax = a['x'] + a['hitbox_offset_x']
    ay = a['y'] + a['hitbox_offset_y']
    bx = b['x'] + b['hitbox_offset_x']
    by = b['y'] + b['hitbox_offset_y']
    return (ax < bx + b['w'] and ax + a['w'] > bx and
            ay < by + b['h'] and ay + a['h'] > by)


def resolve_object_collisions(objects_list):
    """Pass2: детекция + отскок где layers_push."""
    _build_spatial_grid(objects_list)
    processed_pairs = set()

    for obj in objects_list:
        my_layer = obj.get('layer', objects.LAYER_NONE)
        if my_layer == objects.LAYER_NONE:
            continue

        for other in _get_nearby_objects(obj):
            pair_id = tuple(sorted([id(obj), id(other)]))
            if pair_id in processed_pairs:
                continue
            processed_pairs.add(pair_id)

            other_layer = other.get('layer', objects.LAYER_NONE)
            if not (objects.layers_collide(my_layer, other_layer) or
                    objects.layers_collide(other_layer, my_layer)):
                continue
            if not _hitboxes_overlap(obj, other):
                continue

            # Центры хитбоксов
            c1x = obj['x'] + obj['hitbox_offset_x'] + obj['w'] / 2
            c1y = obj['y'] + obj['hitbox_offset_y'] + obj['h'] / 2
            c2x = other['x'] + other['hitbox_offset_x'] + other['w'] / 2
            c2y = other['y'] + other['hitbox_offset_y'] + other['h'] / 2
            dx, dy = c1x - c2x, c1y - c2y
            overlap_x = (obj['w'] + other['w']) / 2 - abs(dx)
            overlap_y = (obj['h'] + other['h']) / 2 - abs(dy)
            if overlap_x <= 0 or overlap_y <= 0:
                continue

            do_push = objects.layers_push(my_layer, other_layer)
            if overlap_x < overlap_y:
                depth = overlap_x
                nx = 1.0 if dx > 0 else -1.0
                ny = 0.0
                if do_push:
                    obj['x'] += nx * depth * 0.5
                    other['x'] -= nx * depth * 0.5
                    if obj['vx'] * nx > 0:
                        obj['vx'] *= -0.3
                    if other['vx'] * (-nx) > 0:
                        other['vx'] *= -0.3
            else:
                depth = overlap_y
                nx = 0.0
                ny = 1.0 if dy > 0 else -1.0
                if do_push:
                    obj['y'] += ny * depth * 0.5
                    other['y'] -= ny * depth * 0.5
                    if obj['vy'] * ny > 0:
                        obj['vy'] *= -0.3
                    if other['vy'] * (-ny) > 0:
                        other['vy'] *= -0.3

            objects.add_collision(obj, 'object', target=other)
            objects.add_collision(other, 'object', target=obj)


def update_physics(objects_list):
    """Полный цикл физики (2 прохода)."""
    objects.clear_collisions(objects_list)

    for obj in objects_list:
        prev_bottom_y = obj['y'] + obj['hitbox_offset_y'] + obj['h']
        if obj.get('has_gravity', True):
            apply_gravity(obj)
        check_static_collision(obj, prev_bottom_y)
        if obj.get('has_friction', True):
            apply_friction(obj)

    resolve_object_collisions(objects_list)
