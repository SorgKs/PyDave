#!/usr/bin/env python3
# debug_tilemap.py — выгружает содержимое tilemap.grid в текстовый файл

import tilemap
import level as lvl
import levels

def dump_grid_to_file(filename="tilemap_dump.txt"):
    # Инициализируем tilemap (он загрузит уровень и построит сетку)
    tilemap.init_tilemap()
    
    # Получаем данные
    grid = tilemap.grid
    rows = tilemap.rows
    cols = tilemap.cols

    if not grid:
        print("❌ Ошибка: tilemap.grid пуст!")
        return

    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"Tilemap grid ({rows} x {cols})\n")
        f.write("=" * 60 + "\n")
        f.write("Легенда:  F = floor   A = air   W = wall   WT = wall_top   step_XX = ступень\n")
        f.write("=" * 60 + "\n\n")

        for y in range(rows):
            row_str = ""
            for x in range(cols):
                name = grid[y][x]
                # Сокращённое представление
                if name == '':
                    row_str += ' . '
                elif name == 'floor':
                    row_str += ' F '
                elif name == 'air':
                    row_str += ' A '
                elif name == 'wall':
                    row_str += ' W '
                elif name == 'wall_top':
                    row_str += 'WT '
                elif name.startswith('step_'):
                    row_str += f'{name[-2:]} '   # например, "00 " или "01 "
                else:
                    row_str += f' ? '  # неожиданное имя
            f.write(row_str + "\n")
    
    print(f"✅ Данные tilemap сохранены в {filename}")

if __name__ == "__main__":
    dump_grid_to_file()
