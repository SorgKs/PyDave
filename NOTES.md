# Тайлы уровня Dangerous Dave

## Стены дома

### Левая стена (внутренняя)
**Файлы:** `wall_left_a.bmp`, `wall_left_b.bmp`  
**Размер:** 16×16 пикселей  
**Использование:** чередуются в шахматном порядке для левой половины стены

### Правая стена (внутренняя)
**Файлы:** зеркальное отражение `wall_left_a.bmp` и `wall_left_b.bmp`  
**Использование:** применяется для правой половины стены

### Обои внутри дома (шахматный порядок)

**Файлы:** `wallpaper_a.bmp`, `wallpaper_b.bmp`  
**Размер:** 16×16 пикселей  
**Использование:** чередуются в шахматном порядке для создания мозаики стен

### Пример сборки стены 10×10

```bash
python assemble.py wallpaper_a wallpaper_b 10 10
Пол этажа (мощение)
Файлы: floor_a.bmp, floor_b.bmp
Размер: 16×16 пикселей
Использование: чередуются в шахматном порядке для создания напольного покрытия

Логика чередования пола:
Если (row + col) % 2 == 0 → floor_a.bmp

Если (row + col) % 2 == 1 → floor_b.bmp

Внешняя область (air)
Файл: air.bmp
Размер: 16×16 пикселей
Использование: мощение всех клеток за пределами дома (область вне стен)

Особенности:
Отрисовывается для всех клеток, не являющихся стенами (X)

Создаёт эффект "пустоты" или внешней среды за стенами

Может быть тёмным фоном, травой или другим ландшафтом

Полная схема отрисовки
Тип клетки	Текстура	Условие
Пустой пол (. внутри дома)	floor_a.bmp / floor_b.bmp (шахматный порядок)	grid[y][x] == 0 и клетка внутри дома
Внешняя область	air.bmp	grid[y][x] == 0 и клетка снаружи дома
Стена (X)	wallpaper_a.bmp / wallpaper_b.bmp (шахматный порядок)	grid[y][x] == 1
Ступень (-)	stair_*.bmp	grid[y][x] == 2
text

---

## 2. Модификация `main.py` для полной отрисовки

Добавьте загрузку всех текстур в секцию ресурсов:

```python
# После загрузки BRICKS / BRICK_TOPS
# Текстуры пола
FLOOR_A = load_image('floor_a.bmp', colorkey=True) if os.path.exists(os.path.join(ASSETS_DIR, 'sprites', 'floor_a.bmp')) else None
FLOOR_B = load_image('floor_b.bmp', colorkey=True) if os.path.exists(os.path.join(ASSETS_DIR, 'sprites', 'floor_b.bmp')) else None

# Текстура внешней области
AIR_TILE = load_image('air.bmp', colorkey=True) if os.path.exists(os.path.join(ASSETS_DIR, 'sprites', 'air.bmp')) else None

# Текстуры стен (левая и правая)
WALL_LEFT_A = load_image('wall_left_a.bmp', colorkey=True) if os.path.exists(os.path.join(ASSETS_DIR, 'sprites', 'wall_left_a.bmp')) else None
WALL_LEFT_B = load_image('wall_left_b.bmp', colorkey=True) if os.path.exists(os.path.join(ASSETS_DIR, 'sprites', 'wall_left_b.bmp')) else None
WALL_RIGHT_A = pygame.transform.flip(WALL_LEFT_A, True, False) if WALL_LEFT_A else None
WALL_RIGHT_B = pygame.transform.flip(WALL_LEFT_B, True, False) if WALL_LEFT_B else None

# Обои для стен (как fallback)
WALLPAPER_A = load_image('wallpaper_a.bmp', colorkey=True) if os.path.exists(os.path.join(ASSETS_DIR, 'sprites', 'wallpaper_a.bmp')) else None
WALLPAPER_B = load_image('wallpaper_b.bmp', colorkey=True) if os.path.exists(os.path.join(ASSETS_DIR, 'sprites', 'wallpaper_b.bmp')) else None
