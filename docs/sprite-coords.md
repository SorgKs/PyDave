# Координаты спрайтов эффектов выстрела

## Источник координат: webdave (GitHub)

Референсная реализация: https://github.com/lightest/webdave
Файлы в репозитории:
- `SparkSFX.js` — координаты искр/огня
- `SmokeSFX.js` — координаты дыма
- `AssetLoader.js` — общий загрузчик

Локальной копии webdave **нет** — все координаты берутся напрямую из исходников
на GitHub (raw.githubusercontent.com/lightest/webdave/master/...).

## Spark (искры)

- Файл: https://raw.githubusercontent.com/lightest/webdave/master/SparkSFX.js
- Координаты: **x=2510, y=0, w=28, h=24**
- 1 кадр, длительность 0.12 с
- Появляется **в точке попадания** (hitPoint), НЕ у дула

## Smoke (дым у дула)

- Файл: https://raw.githubusercontent.com/lightest/webdave/master/SmokeSFX.js
- Размер: **w=16, h=16**
- 6 кадров анимации (3 направления × 2 кадра)
- vy = -30 (дым поднимается вверх)
- Спавнится **у дула**, всегда при выстреле

| Кадр | Направление     | x      |
|------|-----------------|--------|
| 0    | STRAIGHT (0)    | 3135   |
| 1    | STRAIGHT (1)    | 3231   |
| 2    | UP (0)          | 3103   |
| 3    | UP (1)          | 3199   |
| 4    | DOWN (0)        | 3071   |
| 5    | DOWN (1)        | 3167   |

## 6 кадров анимации выстрела (dave.png, y=0)

В локальном атласе `assets/sheets/dave.png` кадры огня и дыма чередуются,
размер **28×24** (same as spark_0 из webdave).

| № | x    | Кадр | Содержимое | Имя      |
|---|------|------|------------|----------|
| 0 | 2510 | 1    | 🔥 огонь   | spark_0  |
| 1 | 2540 | 2    | 🌫️ огонь+дым    | spark_1  |
| 2 | 2570 | 3    | 🔥 огонь   | spark_2  |
| 3 | 2600 | 4    | 🌫️ серый дым    | smoke_0  |
| 4 | 2628 | 5    | 🌫️ серый дым    | smoke_1  |
| 5 | 2660 | 6    | 🌑 чёрный дым    | smoke_2  |

## webdave timeline

1. **SmokeSFX** — спавнится у дула, LIFE_TIME=0.4с, vy=-30 (поднимается вверх)
2. **SparkSFX** — спавнится только в точке попадания (hitPoint), LIFE_TIME=0.12с
3. Dave sprite (shootStraight): 2 кадра с анимацией (animSpeed=5)

## Локальная реализация

`spawn_muzzle_flash()` создаёт одну анимацию из 6 кадров:
```python
['spark_0', 'spark_1', 'spark_2', 'smoke_0', 'smoke_1', 'smoke_2']
```

`spawn_hit_spark()` создаёт отдельный spark_0 в точке попадания.

**Файлы:** `assets/sprites/spark_0..2.bmp`, `assets/sprites/smoke_0..2.bmp`
**Регистрация:** `anims/muzzle.py` через `sprites_map()`