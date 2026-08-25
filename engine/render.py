# engine/render.py — модуль отрисовки
"""
Ответственность:
- Отрисовка тайловой карты уровня
- Отрисовка объектов по координатам
- Работа с камерой
- Никакой логики, только рендеринг

Входные данные:
- tilemap: тайловая карта (2D массив имен спрайтов)
- objects: список объектов с координатами и спрайтами
- camera: параметры камеры (x, y)
- sprites: словарь загруженных спрайтов
"""

import pygame


def render_tilemap(view, tilemap_grid, cam_x, cam_y, ts, sprites, viewport_w, viewport_h):
    """
    Отрисовывает видимую часть тайловой карты.
    
    Args:
        view: поверхность для отрисовки (view surface)
        tilemap_grid: 2D массив имен спрайтов [[sprite_name, ...], ...]
        cam_x, cam_y: позиция камеры
        ts: размер тайла в пикселях
        sprites: словарь {name: pygame.Surface}
        viewport_w, viewport_h: размеры области просмотра
    """
    rows = len(tilemap_grid)
    if rows == 0:
        return
    cols = len(tilemap_grid[0])
    
    # Вычисляем видимый диапазон тайлов
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


def render_objects(view, objects_list, cam_x, cam_y, sprites, get_sprite_func=None):
    """
    Отрисовывает все объекты на экране.
    
    Args:
        view: поверхность для отрисовки
        objects_list: список объектов
        cam_x, cam_y: позиция камеры
        sprites: словарь {name: pygame.Surface}
        get_sprite_func: функция get_sprite(obj) для получения имени спрайта
    """
    for obj in objects_list:
        # Пропускаем объекты вне экрана
        screen_x = obj['x'] + obj['sprite_offset_x'] - cam_x
        screen_y = obj['y'] + obj['sprite_offset_y'] - cam_y
        
        # Быстрая проверка видимости
        if screen_x < -obj['sprite_w'] or screen_x > view.get_width():
            continue
        if screen_y < -obj['sprite_h'] or screen_y > view.get_height():
            continue
        
        # Получаем имя спрайта
        if get_sprite_func:
            sprite_name = get_sprite_func(obj)
        else:
            sprite_name = obj.get('current_sprite')
        
        if not sprite_name:
            continue
        
        sprite = sprites.get(sprite_name)
        if sprite is None:
            continue
        
        # Обработка направления (flip)
        face = obj.get('face', 1)
        if face < 0:
            sprite = pygame.transform.flip(sprite, True, False)
        
        # Обработка мигания (flash)
        alpha = None
        if obj.get('flash', 0) > 0:
            # Можно сделать белую версию спрайта или полупрозрачную
            pass
        
        # Отрисовка
        view.blit(sprite, (int(round(screen_x)), int(round(screen_y))))


def render_decorations(view, decorations, cam_x, cam_y, sprites, gtime=0):
    """
    Отрисовывает декорации (шипы, факелы, предметы).
    
    Args:
        view: поверхность для отрисовки
        decorations: список декораций [{'type': 'spike', 'x': x, 'y': y}, ...]
        cam_x, cam_y: позиция камеры
        sprites: словарь {name: pygame.Surface}
        gtime: глобальный таймер для анимации
    """
    for dec in decorations:
        dec_type = dec.get('type')
        x = dec['x'] - cam_x
        y = dec['y'] - cam_y
        
        if dec_type == 'spike':
            sprite = sprites.get('spike')
            if sprite:
                view.blit(sprite, (int(x), int(y)))
                
        elif dec_type == 'torch':
            # Анимация факела
            seed = dec.get('seed', 0)
            flick = (pygame.math.Vector2(1, 0).rotate(gtime * 0.3 + seed * 10).x * 0.5 + 0.5) * 0.5 + \
                    (pygame.math.Vector2(1, 0).rotate(gtime * 0.13 + seed * 20).x * 0.5 + 0.5) * 0.5
            
            # Рисуем факел процедурно
            pygame.draw.rect(view, pygame.Color('#5a3a20'), (x + 7, y + 9, 2, 5))
            pygame.draw.rect(view, pygame.Color('#3a2412'), (x + 6, y + 13, 4, 2))
            
            fh = 5 + flick * 1.5
            pygame.draw.polygon(view, pygame.Color('#ff8c2e'), 
                              [(x + 5, y + 9), (x + 8, y + 9 - fh * 1.6), (x + 11, y + 9)])
            pygame.draw.polygon(view, pygame.Color('#ffd23f'), 
                              [(x + 6, y + 9), (x + 8, y + 9 - fh), (x + 10, y + 9)])
            pygame.draw.rect(view, pygame.Color('#fff3b0'), (x + 7, y + 7, 2, 2))
            
        elif dec_type == 'gem':
            if dec.get('taken', False):
                continue
            sprite = sprites.get('gem')
            if sprite:
                bob = pygame.math.Vector2(1, 0).rotate(gtime * 0.08 + dec.get('seed', 0) * 10).x * 2
                view.blit(sprite, (int(x), int(y + bob)))
                
        elif dec_type == 'heart':
            if dec.get('taken', False):
                continue
            sprite = sprites.get('heart')
            if sprite:
                scale = 1 + 0.08 * pygame.math.Vector2(1, 0).rotate(gtime * 0.15).x
                scaled_sprite = pygame.transform.scale(
                    sprite, 
                    (int(16 * scale), int(16 * scale))
                )
                view.blit(scaled_sprite, 
                         (int(x - scaled_sprite.get_width() / 2 + 8), 
                          int(y - scaled_sprite.get_height() / 2 + 8)))


def update_camera(cam_x, cam_y, target_x, target_y, viewport_w, viewport_h, 
                  level_width, level_height, smoothing=0.1):
    """
    Плавно обновляет позицию камеры, следуя за целью.
    
    Args:
        cam_x, cam_y: текущая позиция камеры
        target_x, target_y: целевая позиция (обычно центр игрока)
        viewport_w, viewport_h: размеры области просмотра
        level_width, level_height: размеры уровня
        smoothing: коэффициент сглаживания (0.0-1.0)
    
    Returns:
        (new_cam_x, new_cam_y): новая позиция камеры
    """
    new_cam_x = cam_x + (target_x - cam_x) * smoothing
    new_cam_y = cam_y + (target_y - cam_y) * smoothing
    
    # Ограничиваем камеру пределами уровня
    new_cam_x = max(0, min(new_cam_x, level_width - viewport_w))
    new_cam_y = max(0, min(new_cam_y, level_height - viewport_h))
    
    return new_cam_x, new_cam_y
