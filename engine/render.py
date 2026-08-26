# engine/render.py — отрисовка тайлов и объектов от якоря
"""
Только рендер. Спрайт объекта: якорь + размер текущего кадра.
"""

import pygame
from engine import objects as eng_objects


def render_tilemap(view, tilemap_grid, cam_x, cam_y, ts, sprites, viewport_w, viewport_h):
    """Отрисовывает видимую часть тайловой карты (cam/ts в пикселях)."""
    rows = len(tilemap_grid)
    if rows == 0:
        return
    cols = len(tilemap_grid[0])

    x0 = max(0, int(cam_x // ts))
    x1 = min(cols - 1, int((cam_x + viewport_w) // ts) + 1)
    y0 = max(0, int(cam_y // ts))
    y1 = min(rows - 1, int((cam_y + viewport_h) // ts) + 1)

    for ty in range(y0, y1 + 1):
        for tx in range(x0, x1 + 1):
            tile_name = tilemap_grid[ty][tx]
            if not tile_name:
                continue
            sprite = sprites.get(tile_name)
            if sprite is None:
                continue
            px = tx * ts - cam_x
            py = ty * ts - cam_y
            view.blit(sprite, (int(round(px)), int(round(py))))


def render_objects(view, objects_list, cam_x, cam_y, sprites, sprite_keys, ts):
    """
    Рисует объекты.
    sprite_keys: dict id(obj) → ключ спрайта (из transform за кадр).
    obj x/y в тайлах; cam и ts в пикселях.
    """
    for obj in objects_list:
        key = sprite_keys.get(id(obj)) if sprite_keys is not None else obj.get('current_sprite')
        if not key:
            continue
        sprite = sprites.get(key)
        if sprite is None:
            continue

        sw, sh = sprite.get_width(), sprite.get_height()
        screen_x, screen_y = eng_objects.get_sprite_render_pos(
            obj, cam_x, cam_y, sw, sh, ts)

        if screen_x < -sw or screen_x > view.get_width():
            continue
        if screen_y < -sh or screen_y > view.get_height():
            continue

        if obj.get('face', 1) < 0:
            sprite = pygame.transform.flip(sprite, True, False)

        view.blit(sprite, (int(round(screen_x)), int(round(screen_y))))


def update_camera(cam_x, cam_y, target_x, target_y, viewport_w, viewport_h,
                  level_width, level_height, smoothing=0.1):
    """Плавно обновляет камеру (всё в пикселях)."""
    new_cam_x = cam_x + (target_x - cam_x) * smoothing
    new_cam_y = cam_y + (target_y - cam_y) * smoothing
    new_cam_x = max(0, min(new_cam_x, max(0, level_width - viewport_w)))
    new_cam_y = max(0, min(new_cam_y, max(0, level_height - viewport_h)))
    return new_cam_x, new_cam_y
