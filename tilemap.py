# tilemap.py — строит карту имён тайлов по символам из level.py
import level as lvl

class TileMap:
    def __init__(self):
        self.grid = None
        self.rows = 0
        self.cols = 0

    def build(self):
        map_lines = lvl.MAP
        rows = len(map_lines)
        cols = max(len(r) for r in map_lines)
        self.rows = rows
        self.cols = cols
        self.grid = [['' for _ in range(cols)] for _ in range(rows)]

        # Плейсхолдеры объектов — заменяем на фон только при достаточном окружении
        object_placeholders = set('DKSoTdGBHZk')

        def bg_neighbors(y, x):
            """Считает соседей-фон (A или .) в исходной карте."""
            air = wp = 0
            for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < rows and 0 <= nx < cols:
                    nch = map_lines[ny].ljust(cols, '.')[nx]
                    if nch == 'A':
                        air += 1
                    elif nch == '.':
                        wp += 1
            return air + wp, air, wp

        def placeholder_tile(x, y, air, wp):
            if air > wp:
                return 'air'
            return 'wallpaper_a' if (x + y) % 2 == 0 else 'wallpaper_b'

        for y, row in enumerate(map_lines):
            row = row.ljust(cols, '.')  # дополняем точками
            x = 0
            while x < cols:
                ch = row[x]
                if ch == '-':
                    # Находим весь непрерывный блок лестницы в этой строке
                    start_x = x
                    while x < cols and row[x] == '-':
                        x += 1
                    end_x = x - 1
                    width = end_x - start_x + 1
                    
                    # Назначаем тайлы по позиции внутри блока:
                    # 0 → step_00 (левый край)
                    # 1 → step_01
                    # width-2 → step_03
                    # width-1 → step_04 (правый край)
                    # остальные → step_02 (середина)
                    for i in range(width):
                        cx = start_x + i
                        if i == 0:
                            self.grid[y][cx] = 'step_00'
                        elif i == 1:
                            self.grid[y][cx] = 'step_01'
                        elif i == width - 2:
                            self.grid[y][cx] = 'step_03'
                        elif i == width - 1:
                            self.grid[y][cx] = 'step_04'
                        else:
                            self.grid[y][cx] = 'step_02'
                elif ch == 'L':
                    # LL: первый → wall_left_a, второй → wall_left_b (не шахматка)
                    start_x = x
                    while x < cols and row[x] == 'L':
                        x += 1
                    for i in range(x - start_x):
                        name = 'wall_left_a' if i % 2 == 0 else 'wall_left_b'
                        self.grid[y][start_x + i] = name
                elif ch == 'R':
                    # RR: первый → wall_right_a, второй → wall_right_b
                    start_x = x
                    while x < cols and row[x] == 'R':
                        x += 1
                    for i in range(x - start_x):
                        name = 'wall_right_a' if i % 2 == 0 else 'wall_right_b'
                        self.grid[y][start_x + i] = name
                elif ch == 'X':
                    self.grid[y][x] = 'floor'
                    x += 1
                elif ch == 'A':
                    self.grid[y][x] = 'air'
                    x += 1
                elif ch == '.':
                    # Обои – чередуем wallpaper_a / wallpaper_b
                    self.grid[y][x] = 'wallpaper_a' if (x + y) % 2 == 0 else 'wallpaper_b'
                    x += 1
                elif ch in object_placeholders:
                    # Плейсхолдер → фон, если рядом ≥2 клеток воздуха или обоев
                    total, air, wp = bg_neighbors(y, x)
                    if total >= 2:
                        self.grid[y][x] = placeholder_tile(x, y, air, wp)
                    else:
                        self.grid[y][x] = ''
                    x += 1
                else:
                    # Любые другие символы — пустота
                    self.grid[y][x] = ''
                    x += 1

# Глобальные переменные
grid = []
rows = 0
cols = 0
_tilemap = TileMap()

def init_tilemap():
    global grid, rows, cols
    _tilemap.build()
    grid = _tilemap.grid
    rows = _tilemap.rows
    cols = _tilemap.cols