#!/usr/bin/env python3
# debug_surface.py — тестирование surface_map с визуализацией

import sys
import pygame
from surface_map import build_surface_map
from config import WW, WH

# РАЗБЛОКИРУЕМ БУФЕР ВЫВОДА
sys.stdout.reconfigure(line_buffering=True)

def main():
    print("\n" + "=" * 80)
    print("ЗАПУСК DEBUG_SURFACE")
    print("=" * 80 + "\n")
    sys.stdout.flush()
    
    # ВЫЗЫВАЕМ surface_map с включённым выводом в консоль
    surface_grid, rows, cols = build_surface_map(verbose=True)
    
    print("\n" + "=" * 80)
    print("ВИЗУАЛИЗАЦИЯ КАРТЫ ПОВЕРХНОСТЕЙ")
    print("=" * 80 + "\n")
    sys.stdout.flush()
    
    # Инициализация Pygame для визуализации (без шрифтов)
    pygame.init()
    
    screen = pygame.display.set_mode((WW, WH))
    pygame.display.set_caption(f"Debug: Surface Map {rows}×{cols}")
    clock = pygame.time.Clock()

    # Размер клетки на виртуальном экране
    cell_size = 16
    view_w = min(cols * cell_size, 1600)
    view_h = min(rows * cell_size, 1200)
    view = pygame.Surface((view_w, view_h))

    # Цвета для разных типов
    COLOR_EMPTY = (0, 0, 0)          # 0 – пустота
    COLOR_SOLID = (180, 180, 180)    # 1 – твёрдая
    COLOR_PLATFORM = (0, 200, 200)   # 2 – платформа

    # Рисуем сетку
    for y in range(rows):
        for x in range(cols):
            val = surface_grid[y][x]
            if val == 0:
                color = COLOR_EMPTY
            elif val == 1:
                color = COLOR_SOLID
            elif val == 2:
                color = COLOR_PLATFORM
            else:
                color = (255, 0, 255)

            rect = pygame.Rect(x * cell_size, y * cell_size, cell_size, cell_size)
            pygame.draw.rect(view, color, rect)
            pygame.draw.rect(view, (50, 50, 50), rect, 1)

    # Масштабируем карту
    scale_x = WW / view_w
    scale_y = WH / view_h
    scale = min(scale_x, scale_y, 3.0)
    new_w = int(view_w * scale)
    new_h = int(view_h * scale)
    scaled = pygame.transform.scale(view, (new_w, new_h))

    # Центрируем
    offset_x = (WW - new_w) // 2
    offset_y = (WH - new_h) // 2

    print("🖥️ Отображение карты поверхностей. Нажмите ESC или закройте окно для выхода.")
    sys.stdout.flush()
    
    running = True
    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    running = False

        screen.fill((30, 30, 30))
        screen.blit(scaled, (offset_x, offset_y))
        
        # Простая легенда без шрифтов (цветные квадраты)
        legend_items = [
            ("Пустота (0)", COLOR_EMPTY),
            ("Твёрдая (1)", COLOR_SOLID),
            ("Платформа (2)", COLOR_PLATFORM)
        ]
        legend_x = 10
        legend_y = 10
        for label, color in legend_items:
            pygame.draw.rect(screen, color, (legend_x, legend_y, 20, 20))
            pygame.draw.rect(screen, (200, 200, 200), (legend_x, legend_y, 20, 20), 1)
            legend_y += 25
        
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
