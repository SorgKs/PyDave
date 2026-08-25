# Engine — новый игровой движок (рефакторинг)

## Архитектура

```
engine/
├── __init__.py      # Точка входа, экспорт модулей
├── objects.py       # Модуль объектов (anims/obj)
│   ├── create_object()
│   ├── compute_offsets()
│   ├── init()       # Инициализация объекта из данных уровня
│   ├── behave()     # Логика поведения (ввод, ИИ)
│   ├── transform()  # Реакция на коллизии
│   └── get_sprite() # Получение спрайта для рендера
├── physics.py       # Универсальная физика
│   ├── init_physics()
│   ├── update_physics()  # 2 прохода: статика + межобъектные
│   └── resolve_object_collisions()
└── render.py        # Отрисовка
    ├── render_tilemap()
    ├── render_objects()
    └── update_camera()
```

## Игровой цикл

```python
# 1. Загрузка
surface_grid = build_surface_map(level.MAP)
engine.physics.init_physics(TS, surface_grid, ROWS, COLS)
objects = [engine.objects.create_object(...) for ...]

# 2. Цикл игры
while running:
    # A. Поведение (input + AI)
    for obj in objects:
        engine.objects.behave(obj, input_state, triggers)
    
    # B. Физика (2 прохода)
    engine.physics.update_physics(objects)
    
    # C. Трансформация (реакция на коллизии)
    for obj in objects:
        if obj['collisions']:
            engine.objects.transform(obj)
    
    # D. Рендер
    camera = engine.render.update_camera(...)
    engine.render.render_tilemap(view, tilemap, camera, ...)
    engine.render.render_objects(view, objects, camera, sprites)
```

## Ключевые особенности

### 1. Смещения хитбокса и спрайта
- `hitbox_offset_x/y`: смещение хитбокса относительно (x, y)
- `sprite_offset_x/y`: смещение спрайта относительно (x, y)
- Вычисляются один раз при инициализации через `compute_offsets()`

### 2. Типы якорей (Anchor Types)
- `ANCHOR_BOTTOM_CENTER`: x,y = середина низа (игрок, наземные враги)
- `ANCHOR_CENTER`: x,y = центр (летающие объекты)

### 3. Слои коллизий
- `LAYER_PLAYER`: игрок
- `LAYER_ENEMY`: враги (отталкивают игрока и друг друга)
- `LAYER_ITEM`: предметы (только гравитация, нет межобъектных коллизий)
- `LAYER_TRIGGER`: триггеры (сквозные)

### 4. Двухпроходная физика
- **Pass 1**: гравитация + коллизии со статикой
- **Pass 2**: разрешение межобъектных коллизий с отталкиванием

### 5. Детальные коллизии
После физики в `obj['collisions']`:
```python
{
    'target': other_obj,  # или None для статики
    'normal': (nx, ny),   # нормаль
    'depth': 5.2,         # глубина проникновения
    'point': (px, py),    # точка контакта
    'type': 'object'      # или 'static'
}
```

## Миграция со старого кода

1. Перенести логику из `anims/dave.py`, `anims/zombie.py` и т.д. в новые функции `behave()` и `transform()`
2. Заменить вызовы `physics.update_player_physics()` на `engine.physics.update_physics()`
3. Использовать `engine.objects.get_hitbox_rect()` вместо ручного создания Rect
4. Перенести отрисовку в `engine.render.render_*()` функции
