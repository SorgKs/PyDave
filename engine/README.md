# Engine — игровой движок (api-decisions.md)

## Архитектура

```
anims/                 # фабрика + логика типов (dict + функции)
├── create_object()
├── behave(obj, keys, map)
├── transform(obj) → sprite_key
└── <type>.py          # init, behave, transform, sprites_map

engine/
├── objects.py         # хелперы (hitbox, layers, collisions) — без фабрики
├── physics.py         # 2 прохода, единицы — тайлы
└── render.py          # тайлы + объекты от якоря
```

## Игровой цикл

```python
# старт: assets грузит тайлы + sprites_map типов
# парсер: create_object → готовые объекты (тайлы)

for obj in objects:
    behave(obj, keys, surface_grid)   # keys: 'l+', 'l=', 'j+', …

physics.update_physics(objects)       # pass1 статика; pass2 объекты + отскок

for obj in objects:
    sprite_key = transform(obj)       # каждый кадр; чистит collisions
# render: sprites[sprite_key], якорь + размер кадра
```

## Контракты

| Функция     | pos | vel | визуал / face | внутренние поля | collisions        |
|-------------|-----|-----|---------------|-----------------|-------------------|
| `behave`    | нет | да  | face ок       | по необходимости| не трогает        |
| `physics`   | да  | да  | нет           | нет             | заполняет         |
| `transform` | нет | нет | спрайт/оффсет | да              | читает и очищает  |

- Единицы `behave` / `physics`: **тайлы** (`TS` только в render/assets)
- `layer`: одно int (не битовая маска)
- `anchor_type`: `'ground'` | `'center'`
- `keys`: токены `код+` (edge) / `код=` (hold)
