# aim.py — расчёт выстрела и поиск целей
import math
import pygame
from config import TS
import level as lvl


def find_target_in_cone(player, enemies, surface_grid, ROWS, COLS, cone_angle=15):
    """
    Ищет ближайшую цель в конусе 15 градусов.
    Возвращает: (target, hit_pos, hit_type)
    - target: объект противника или None
    - hit_pos: (x, y) точка попадания
    - hit_type: 'enemy', 'wall', 'floor', None
    """
    # Начальная точка выстрела (центр хитбокса)
    start_x = player['x'] + player['w'] / 2
    start_y = player['y'] + player['h'] / 2
    direction = player['face']  # -1 или 1

    # Проверяем всех врагов
    best_dist = float('inf')
    best_enemy = None
    best_hit = None

    # Преобразуем угол в радианы
    cone_rad = math.radians(cone_angle)

    for enemy in enemies:
        # Центр врага
        enemy_x = enemy['x'] + enemy['w'] / 2
        enemy_y = enemy['y'] + enemy['h'] / 2

        # Вектор от игрока к врагу
        dx = enemy_x - start_x
        dy = enemy_y - start_y
        dist = math.hypot(dx, dy)

        if dist < 1:
            continue

        # Угол между направлением выстрела и вектором к врагу
        angle = math.atan2(dy, dx)
        face_angle = 0 if direction > 0 else math.pi
        diff = abs(angle - face_angle)

        # Нормализация угла
        if diff > math.pi:
            diff = 2 * math.pi - diff

        if diff <= cone_rad:
            # Проверяем, есть ли стена между игроком и врагом (raycast)
            hit_wall = raycast(start_x, start_y, enemy_x, enemy_y, surface_grid, ROWS, COLS)
            if not hit_wall:
                if dist < best_dist:
                    best_dist = dist
                    best_enemy = enemy
                    best_hit = (enemy_x, enemy_y)

    # Если враг найден
    if best_enemy:
        return best_enemy, best_hit, 'enemy'

    # Если врагов нет, ищем стену или пол в направлении выстрела
    # Проверяем дальность до 200 пикселей (условно)
    max_dist = 200
    step = 2
    for dist in range(0, max_dist, step):
        tx = start_x + direction * dist
        ty = start_y
        # Небольшой разброс по Y (конус)
        for y_offset in range(-int(dist * math.tan(cone_rad)), int(dist * math.tan(cone_rad)) + 1, step):
            check_y = start_y + y_offset
            tile_x = int(tx // TS)
            tile_y = int(check_y // TS)
            if 0 <= tile_x < COLS and 0 <= tile_y < ROWS:
                if surface_grid[tile_y][tile_x] == 1:
                    # Стена
                    return None, (tx, check_y), 'wall'
                if surface_grid[tile_y][tile_x] == 0:
                    # Пол (пустота) — считаем попаданием в пол
                    return None, (tx, check_y), 'floor'

    return None, None, None


def raycast(start_x, start_y, end_x, end_y, surface_grid, ROWS, COLS):
    """Проверяет, есть ли стена между двумя точками."""
    dx = end_x - start_x
    dy = end_y - start_y
    dist = math.hypot(dx, dy)
    if dist < 1:
        return False

    steps = int(dist / 2)  # шаг 2 пикселя
    for i in range(steps + 1):
        t = i / steps
        x = start_x + dx * t
        y = start_y + dy * t
        tile_x = int(x // TS)
        tile_y = int(y // TS)
        if 0 <= tile_x < COLS and 0 <= tile_y < ROWS:
            if surface_grid[tile_y][tile_x] == 1:
                return True
    return False
