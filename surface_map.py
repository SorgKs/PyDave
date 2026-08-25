# surface_map.py — строит карту поверхностей для физики (коллизий) с выводом решения
import level as lvl

def build_surface_map(verbose=True):
    """
    Анализирует level.MAP и возвращает:
    - surface_grid: список списков int (0, 1, 2)
    - rows: количество строк
    - cols: количество столбцов
    
    Если verbose=True, выводит подробный лог в консоль для каждой клетки.
    """
    map_lines = lvl.MAP
    rows = len(map_lines)
    cols = max(len(r) for r in map_lines)

    # Инициализируем сетку нулями (пустота)
    surface_grid = [[0] * cols for _ in range(rows)]

    if verbose:
        print("🔍 ПОДРОБНЫЙ ЛОГ КАРТЫ ПОВЕРХНОСТЕЙ", flush=True)
        print("=" * 80, flush=True)
        print(f"Размер карты: {rows} строк × {cols} столбцов", flush=True)
        print("Легенда: 0 = пустота, 1 = твёрдая (пол/стены), 2 = платформа (лестница)", flush=True)
        print("=" * 80, flush=True)
        print("Формат: [строка][столбец] 'символ' → значение | Решение: пояснение", flush=True)
        print("-" * 80, flush=True)

    for y, row in enumerate(map_lines):
        row = row.ljust(cols, '.')
        for x, ch in enumerate(row):
            # ОПРЕДЕЛЯЕМ ТИП ПОВЕРХНОСТИ
            if ch == 'L' or ch == 'R':
                surface_grid[y][x] = 1
                solution = "стена → твёрдая (1)"
            elif ch == 'X':
                surface_grid[y][x] = 1
                solution = "пол → твёрдая (1)"
            elif ch == '-':
                surface_grid[y][x] = 2
                solution = "лестница → платформа (2)"
            else:
                # ВСЁ ОСТАЛЬНОЕ – ПУСТОТА (0)
                surface_grid[y][x] = 0
                if ch == 'A':
                    solution = "воздух → пустота (0)"
                elif ch == '.':
                    solution = "обои → пустота (0)"
                elif ch == 'D':
                    solution = "выходная дверь → пустота (0)"
                elif ch == 'K':
                    solution = "ключ → пустота (0)"
                elif ch == 'S':
                    solution = "старт → пустота (0)"
                elif ch == 'o':
                    solution = "кубок → пустота (0)"
                elif ch == 'T':
                    solution = "факел → пустота (0)"
                elif ch == 'd':
                    solution = "декоративная дверь → пустота (0)"
                elif ch == '^':
                    solution = "шип → пустота (0)"
                elif ch == 'H':
                    solution = "сердце → пустота (0)"
                elif ch == 'k':
                    solution = "череп → пустота (0)"
                else:
                    solution = f"неизвестный символ '{ch}' → пустота (0) [по умолчанию]"

            if verbose:
                print(f"[{y:3d}][{x:3d}] '{ch}' → {surface_grid[y][x]} | Решение: {solution}", flush=True)

    # Статистика
    counts = {0: 0, 1: 0, 2: 0}
    for y in range(rows):
        for x in range(cols):
            counts[surface_grid[y][x]] += 1

    if verbose:
        print("-" * 80, flush=True)
        print("СТАТИСТИКА:", flush=True)
        print(f"  Пустых клеток (0): {counts[0]}", flush=True)
        print(f"  Твёрдых клеток (1): {counts[1]}", flush=True)
        print(f"  Платформ (2): {counts[2]}", flush=True)
        print(f"  Всего клеток: {rows * cols}", flush=True)
        print("=" * 80, flush=True)

    return surface_grid, rows, cols
