# engine/objects.py — модуль объектов (anims/obj в новой архитектуре)
"""
Ответственность:
- Хранение состояния объекта
- Функции init, behave, transform, get_sprite
- Смещения хитбокса и спрайта относительно (x, y)
- Типы якорей для разных объектов
"""

import pygame

# ============================================================================
# ТИПЫ ЯКОРЕЙ (Anchor Types)
# ============================================================================
# Определяют, как позиция (x, y) соотносится со спрайтом и хитбоксом

ANCHOR_BOTTOM_CENTER = 'bottom_center'  # x,y = середина низа (игрок, наземные враги, падающие)
ANCHOR_CENTER = 'center'                # x,y = центр (летающие, левитирующие объекты)

# ============================================================================
# СЛОИ КОЛЛИЗИЙ (Collision Layers)
# ============================================================================

LAYER_NONE   = 0b00000
LAYER_PLAYER = 0b00001
LAYER_ENEMY  = 0b00010
LAYER_ITEM   = 0b00100  # Предметы (монеты, ключи, бонусы)
LAYER_TRIGGER = 0b01000 # Триггеры (зоны событий)

# Матрица коллизий: какие слои взаимодействуют друг с другом
# Bitmask для каждого слоя: с какими слоями он сталкивается
COLLISION_MATRIX = {
    LAYER_PLAYER: LAYER_ENEMY | LAYER_ITEM | LAYER_TRIGGER,  # Игрок сталкивается с врагами, предметами, триггерами
    LAYER_ENEMY:  LAYER_PLAYER | LAYER_ENEMY,                # Враги отталкивают игрока и друг друга
    LAYER_ITEM:   LAYER_NONE,                                 # Предметы не имеют межобъектных коллизий (только со статикой)
    LAYER_TRIGGER: LAYER_NONE,                                # Триггеры сквозные
}

# ============================================================================
# КОНСТАНТЫ ФИЗИКИ
# ============================================================================

GRAVITY = 0.4
MAX_FALL_SPEED = 10.0
FRICTION_GROUND = 0.8
FRICTION_AIR = 0.3
MIN_SPEED = 0.1

# ============================================================================
# СТРУКТУРА ОБЪЕКТА
# ============================================================================

def create_object(obj_type, x, y, params=None):
    """
    Создает новый объект с правильными смещениями и параметрами.
    
    Args:
        obj_type: тип объекта ('player', 'enemy_zombie', 'enemy_goblin', 'item_gem', 'trigger')
        x, y: координаты спавна
        params: дополнительные параметры (hp, speed, etc.)
    
    Returns:
        dict: объект с полной структурой
    """
    obj = {
        'type': obj_type,
        'x': float(x),
        'y': float(y),
        'vx': 0.0,
        'vy': 0.0,
        'w': 0,  # ширина хитбокса (заполняется в init)
        'h': 0,  # высота хитбокса (заполняется в init)
        'sprite_w': 0,  # ширина спрайта (заполняется в init)
        'sprite_h': 0,  # высота спрайта (заполняется в init)
        'hitbox_offset_x': 0.0,  # смещение хитбокса относительно (x, y)
        'hitbox_offset_y': 0.0,
        'sprite_offset_x': 0.0,  # смещение спрайта относительно (x, y)
        'sprite_offset_y': 0.0,
        'anchor_type': ANCHOR_BOTTOM_CENTER,  # тип якоря
        'state': 'idle',  # текущее состояние анимации
        'face': 1,  # направление (1 = вправо, -1 = влево)
        'onG': False,  # на земле ли
        'collisions': [],  # список коллизий после физики
        'layer': LAYER_NONE,  # слой коллизий
        'custom': params or {},  # пользовательские данные (hp, таймеры, etc.)
        'flash': 0,  # мигание при уроне
        't': 0,  # внутренний таймер
    }
    
    return obj


def compute_offsets(obj, sprite_w, sprite_h, hitbox_w, hitbox_h, anchor_type):
    """
    Вычисляет и устанавливает смещения хитбокса и спрайта относительно (x, y).
    
    Вызывается один раз при инициализации или при смене спрайта.
    
    Args:
        obj: объект
        sprite_w, sprite_h: размеры спрайта
        hitbox_w, hitbox_h: размеры хитбокса
        anchor_type: тип якоря (ANCHOR_BOTTOM_CENTER или ANCHOR_CENTER)
    """
    obj['sprite_w'] = sprite_w
    obj['sprite_h'] = sprite_h
    obj['w'] = hitbox_w
    obj['h'] = hitbox_h
    obj['anchor_type'] = anchor_type
    
    if anchor_type == ANCHOR_BOTTOM_CENTER:
        # x,y = середина низа хитбокса
        # Спрайт рисуется так, чтобы его низ был на уровне y
        obj['hitbox_offset_x'] = -hitbox_w / 2.0
        obj['hitbox_offset_y'] = -hitbox_h
        obj['sprite_offset_x'] = -sprite_w / 2.0
        obj['sprite_offset_y'] = -sprite_h
        
    elif anchor_type == ANCHOR_CENTER:
        # x,y = центр спрайта и хитбокса
        obj['hitbox_offset_x'] = -hitbox_w / 2.0
        obj['hitbox_offset_y'] = -hitbox_h / 2.0
        obj['sprite_offset_x'] = -sprite_w / 2.0
        obj['sprite_offset_y'] = -sprite_h / 2.0


def get_hitbox_rect(obj):
    """Возвращает pygame.Rect хитбокса в мировых координатах."""
    return pygame.Rect(
        int(obj['x'] + obj['hitbox_offset_x']),
        int(obj['y'] + obj['hitbox_offset_y']),
        int(obj['w']),
        int(obj['h'])
    )


def get_sprite_render_pos(obj, cam_x, cam_y):
    """
    Возвращает позицию для отрисовки спрайта с учетом камеры.
    
    Returns:
        (render_x, render_y): координаты верхнего левого угла спрайта
    """
    render_x = obj['x'] + obj['sprite_offset_x'] - cam_x
    render_y = obj['y'] + obj['sprite_offset_y'] - cam_y
    return render_x, render_y


# ============================================================================
# ФУНКЦИИ ИНТЕРФЕЙСА (вызываются из игрового цикла)
# ============================================================================

def init(obj, level_data):
    """
    Инициализирует объект из данных уровня.
    
    Устанавливает:
    - Размеры хитбокса и спрайта
    - Смещения (hitbox_offset, sprite_offset)
    - Слой коллизий
    - Начальное состояние
    
    Args:
        obj: объект для инициализации
        level_data: данные из плейсхолдера уровня (params)
    
    Returns:
        list: имена файлов спрайтов для загрузки (например, ['zombie_walk1', 'zombie_walk2'])
    """
    # Эта функция будет переопределена для каждого типа объекта в anims/
    # Здесь заглушка
    raise NotImplementedError("init() должен быть реализован для каждого типа объекта")


def behave(obj, input_state, level_triggers, dt=1.0):
    """
    Обновляет логику поведения объекта.
    
    Изменяет:
    - obj['vx'], obj['vy']: желаемая скорость
    - obj['state']: состояние для анимации
    - obj['face']: направление
    
    НЕ изменяет obj['x'], obj['y'] напрямую — это делает физика!
    
    Args:
        obj: объект
        input_state: состояние ввода (клавиши, мышь)
        level_triggers: список триггеров уровня
        dt: delta time (для плавности)
    """
    # Эта функция будет переопределена для каждого типа объекта
    pass


def transform(obj):
    """
    Обрабатывает реакции на коллизии.
    
    Вызывается ПОСЛЕ физики для объектов, у которых obj['collisions'] не пуст.
    
    Анализирует список коллизий и принимает решения:
    - Получить урон от врага
    - Подобрать предмет
    - Активировать триггер
    - Отскочить от стены
    
    Args:
        obj: объект со списком коллизий
    """
    # Эта функция будет переопределена для каждого типа объекта
    pass


def get_sprite(obj):
    """
    Возвращает имя текущего спрайта для отрисовки.
    
    Основано на obj['state'], obj['face'], obj['t'].
    
    Args:
        obj: объект
    
    Returns:
        str: имя спрайта (например, 'zombie_walk1')
    """
    # Эта функция будет переопределена для каждого типа объекта
    return None


# ============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================================

def clear_collisions(objects):
    """Очищает списки коллизий у всех объектов перед новым кадром."""
    for obj in objects:
        obj['collisions'] = []


def add_collision(obj, target, normal, depth, point, collision_type='object'):
    """
    Добавляет запись о коллизии в объект.
    
    Args:
        obj: объект, с которым произошло столкновение
        target: второй объект (или None для статики)
        normal: нормаль коллизии (nx, ny)
        depth: глубина проникновения
        point: точка контакта (px, py)
        collision_type: 'object' (межобъектная) или 'static' (со стеной)
    """
    obj['collisions'].append({
        'target': target,
        'normal': normal,
        'depth': depth,
        'point': point,
        'type': collision_type,
    })
