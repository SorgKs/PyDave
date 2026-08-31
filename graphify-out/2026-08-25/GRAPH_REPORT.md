# Graph Report - Dave  (2026-08-25)

## Corpus Check
- 42 files · ~47,672 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 348 nodes · 430 edges · 26 communities (23 shown, 3 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 5 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d73f4e15`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- engine/physics.py
- dave.py
- main.py
- physics.py
- Концепт-документ: Рефакторинг игрового движка
- text.py
- level.py
- anims/__init__.py
- NOTES.md
- API объектов — открытые вопросы
- Ключевые особенности
- convert.py
- render.py
- crop_and_pad.py
- API объектов — зафиксированные решения
- process_doors.py
- test.py
- pad_to_grid.py
- find_atlas.py
- door2.py
- open_doors.py
- split_dave.py
- split_step_tiles
- trim_png.py

## God Nodes (most connected - your core abstractions)
1. `API объектов — зафиксированные решения` - 15 edges
2. `API объектов — открытые вопросы` - 10 edges
3. `update_physics()` - 8 edges
4. `font()` - 8 edges
5. `register_object_type()` - 7 edges
6. `resolve_object_collisions()` - 7 edges
7. `update()` - 7 edges
8. `C()` - 7 edges
9. `Концепт-документ: Рефакторинг игрового движка` - 7 edges
10. `check_static_collision()` - 6 edges

## Surprising Connections (you probably didn't know these)
- `main()` --calls--> `build_surface_map()`  [EXTRACTED]
  debug_surface.py → surface_map.py
- `update()` --calls--> `get_hitbox_rect()`  [EXTRACTED]
  main.py → engine/objects.py
- `update()` --calls--> `update_physics()`  [EXTRACTED]
  main.py → engine/physics.py
- `render()` --calls--> `C()`  [EXTRACTED]
  main.py → text.py
- `render()` --calls--> `font()`  [EXTRACTED]
  main.py → text.py

## Import Cycles
- None detected.

## Communities (26 total, 3 thin omitted)

### Community 0 - "engine/physics.py"
Cohesion: 0.06
Nodes (42): add_collision(), behave(), clear_collisions(), compute_offsets(), create_object(), get_hitbox_rect(), get_sprite(), get_sprite_render_pos() (+34 more)

### Community 1 - "dave.py"
Cohesion: 0.06
Nodes (16): behave(), get_sprite(), init(), Обработка коллизий для Дэйва., Возвращает имя текущего спрайта., Инициализация объекта Дэйв., Логика управления Дэйвом., transform() (+8 more)

### Community 2 - "main.py"
Cohesion: 0.09
Nodes (32): create_object(), Создает новый объект-словарь. Returns: dict: объект со всеми необходимыми полями, load_all_sounds(), load_all_sprites(), load_image(), load_sound(), make_white_variant(), Создаёт "ослепляющую" копию спрайта (для эффекта попадания). (+24 more)

### Community 3 - "physics.py"
Cohesion: 0.09
Nodes (24): apply_friction(), apply_gravity(), distance(), init_physics(), move_x(), move_y(), p_rect(), p_rect_pygame() (+16 more)

### Community 4 - "Концепт-документ: Рефакторинг игрового движка"
Cohesion: 0.10
Nodes (20): 1.1. `anims/obj` (Объекты и Логика), 1.2. `physics` (Физика и Коллизии), 1.3. `anims/obj` (Трансформация), 1.3. `render` (Отрисовка), 1. Архитектурные модули, 2. Поток данных (Game Loop), 3. Вопросы для обсуждения (Critical Design Decisions), 4. Детали реализации смещений (Offsets) (+12 more)

### Community 5 - "text.py"
Cohesion: 0.14
Nodes (20): C(), draw_centered_text(), draw_centered_text_xy(), font(), get_font_ok(), init_font(), overlay(), Инициализация системы шрифтов (+12 more)

### Community 6 - "level.py"
Cohesion: 0.15
Nodes (10): find_target_in_cone(), Проверяет, есть ли стена между двумя точками., Ищет ближайшую цель в конусе 15 градусов. Возвращает: (target, hit_pos,…, raycast(), main(), dump_grid_to_file(), build_surface_map(), Анализирует level.MAP и возвращает: - surface_grid: список списков int (0, 1,… (+2 more)

### Community 7 - "anims/__init__.py"
Cohesion: 0.15
Nodes (12): behave(), _build_type_to_mod(), compute_offsets(), frame(), get_sprite(), Вызывает функцию behave для данного типа объекта., Вызывает функцию transform для данного типа объекта., Вызывает функцию get_sprite для данного типа объекта. (+4 more)

### Community 8 - "NOTES.md"
Cohesion: 0.17
Nodes (11): Левая стена (внутренняя), Обои внутри дома (шахматный порядок), Обои для стен (как fallback), После загрузки BRICKS / BRICK_TOPS, Правая стена (внутренняя), Пример сборки стены 10×10, Стены дома, Тайлы уровня Dangerous Dave (+3 more)

### Community 9 - "API объектов — открытые вопросы"
Cohesion: 0.18
Nodes (10): API объектов — открытые вопросы, Q1. Как `transform` отдаёт спрайт рендеру? — закрыт, Q2. Формат `keys` для `behave` — закрыт, Q3. Формат `map` и `triggers` — закрыт, Q4. Vel / face в `transform` — закрыт, Q5. Поля dict — закрыт, Q6. Типы с карты — закрыт, Q7. Гравитация / трение — закрыт (+2 more)

### Community 10 - "Ключевые особенности"
Cohesion: 0.18
Nodes (10): 1. Смещения хитбокса и спрайта, 2. Типы якорей (Anchor Types), 3. Слои коллизий, 4. Двухпроходная физика, 5. Детальные коллизии, Engine — новый игровой движок (рефакторинг), Архитектура, Игровой цикл (+2 more)

### Community 11 - "convert.py"
Cohesion: 0.29
Nodes (7): autocut(), cut_from(), draw_rect(), draw_text(), Нарезает связные области по сетке (для deaths-of-dave.png — 5 кадров 48x48)., set_px(), write_bmp()

### Community 12 - "render.py"
Cohesion: 0.22
Nodes (8): Отрисовывает декорации (шипы, факелы, предметы). Args: view: поверхность для…, Плавно обновляет позицию камеры, следуя за целью. Args: cam_x, cam_y: текущая…, Отрисовывает видимую часть тайловой карты. Args: view: поверхность для…, Отрисовывает все объекты на экране. Args: view: поверхность для отрисовки…, render_decorations(), render_objects(), render_tilemap(), update_camera()

### Community 13 - "crop_and_pad.py"
Cohesion: 0.25
Nodes (4): crop_to_content(), pad_to_grid(), Находит bounding box непрозрачных пикселей и обрезает., Дополняет до кратного 16: по центру горизонтально, прижата вниз.

### Community 14 - "API объектов — зафиксированные решения"
Cohesion: 0.12
Nodes (15): 10. Гравитация и трение (решение Q7), 11. `compute_offsets` (решение Q8.1), 12. Сигнатура `init` (решение Q8.2), 13. Значения `anchor_type` (решение Q8.3), 14. `layer` (уточнение), 1. Модель объекта, 2. Фабрика и владение структурой, 3. `behave` (+7 more)

### Community 15 - "process_doors.py"
Cohesion: 0.39
Nodes (7): crop_to_content(), pad_to_grid(), process_door(), Находит bounding box непрозрачных пикселей и обрезает., Дополняет до кратного 16: по центру горизонтально, прижата вниз., read_bmp(), write_bmp()

### Community 16 - "test.py"
Cohesion: 0.29
Nodes (4): cut_section(), is_empty(), Тайл пустой, если ВСЕ пиксели прозрачные (alpha < 128)., write_bmp()

### Community 17 - "pad_to_grid.py"
Cohesion: 0.29
Nodes (4): find_input(), pad_to_grid(), Дополняет до кратного 16: по центру горизонтально, прижата вниз., Ищет файл в нескольких местах.

### Community 18 - "find_atlas.py"
Cohesion: 0.47
Nodes (5): download_js_file(), main(), Скачивает содержимое JS-файла, Ищет паттерны определения атласа в JS-коде, search_for_atlas_patterns()

### Community 19 - "door2.py"
Cohesion: 0.70
Nodes (4): assemble_door(), find_tile(), read_bmp(), write_bmp()

### Community 22 - "split_step_tiles"
Cohesion: 0.67
Nodes (3): main(), Нарезает step.bmp (96×16) на тайлы. Структура (6 тайлов по 16 пикселей): [0]…, split_step_tiles()

## Knowledge Gaps
- **56 isolated node(s):** `_Ctx`, `Левая стена (внутренняя)`, `Правая стена (внутренняя)`, `Обои внутри дома (шахматный порядок)`, `Пример сборки стены 10×10` (+51 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `create_object()` connect `main.py` to `anims/__init__.py`?**
  _High betweenness centrality (0.032) - this node is a cross-community bridge._
- **Why does `register_object_type()` connect `dave.py` to `anims/__init__.py`?**
  _High betweenness centrality (0.012) - this node is a cross-community bridge._
- **Why does `update()` connect `main.py` to `engine/physics.py`?**
  _High betweenness centrality (0.009) - this node is a cross-community bridge._
- **What connects `_Ctx`, `Левая стена (внутренняя)`, `Правая стена (внутренняя)` to the rest of the system?**
  _56 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `engine/physics.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05919661733615222 - nodes in this community are weakly interconnected._
- **Should `dave.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05855855855855856 - nodes in this community are weakly interconnected._
- **Should `main.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08771929824561403 - nodes in this community are weakly interconnected._