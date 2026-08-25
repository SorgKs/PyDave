#!/usr/bin/env python3
"""
anims/__init__.py — Базовый класс и реестр объектов.
Каждый тип объекта имеет свой модуль (dave.py, zombie.py и т.д.)

НОВАЯ АРХИТЕКТУРА: Объекты - это словари (dict), а не классы.
Функции init, behave, transform, get_sprite определяются в каждом модуле.
"""

# Реестр функций для каждого типа объекта
OBJECT_TYPES = {}

def register_object_type(name, init_func=None, behave_func=None, transform_func=None, get_sprite_func=None, 
                         hitbox=None, anchor_type='ground', layer=0, tags=None):
    """
    Регистрирует тип объекта с его функциями.
    
    Args:
        name: имя типа ('dave', 'zombie', etc.)
        init_func: функция инициализации(obj, params)
        behave_func: функция поведения(obj, input_data, ctx)
        transform_func: функция обработки коллизий(obj)
        get_sprite_func: функция получения спрайта(obj)
        hitbox: (width, height) хитбокса
        anchor_type: 'ground' или 'center'
        layer: слой коллизий
        tags: список тегов ['solid', 'damage', 'collectible']
    """
    OBJECT_TYPES[name] = {
        'init': init_func,
        'behave': behave_func,
        'transform': transform_func,
        'get_sprite': get_sprite_func,
        'hitbox': hitbox or (32, 32),
        'anchor_type': anchor_type,
        'layer': layer,
        'tags': tags or [],
    }


def create_object(obj_type, x, y, params=None):
    """
    Создает новый объект-словарь.
    
    Returns:
        dict: объект со всеми необходимыми полями
    """
    if obj_type not in OBJECT_TYPES:
        raise ValueError(f"Не найден тип объекта: {obj_type}")
    
    type_data = OBJECT_TYPES[obj_type]
    hitbox_w, hitbox_h = type_data['hitbox']
    anchor = type_data['anchor_type']
    
    # Создаем базовую структуру объекта
    obj = {
        'type': obj_type,
        'x': float(x),
        'y': float(y),
        'vx': 0.0,
        'vy': 0.0,
        'w': hitbox_w,
        'h': hitbox_h,
        'sprite_w': hitbox_w,  # Будет обновлено при загрузке спрайта
        'sprite_h': hitbox_h,
        'hitbox_offset_x': 0.0,
        'hitbox_offset_y': 0.0,
        'sprite_offset_x': 0.0,
        'sprite_offset_y': 0.0,
        'anchor_type': anchor,
        'state': 'idle',
        'face': 1,
        'onG': False,
        'collisions': [],
        'layer': type_data['layer'],
        'tags': type_data['tags'].copy(),
        'custom': params or {},
        'flash': 0,
        't': 0,
    }
    
    # Вычисляем смещения
    compute_offsets(obj, hitbox_w, hitbox_h, hitbox_w, hitbox_h, anchor)
    
    # Вызываем функцию инициализации типа
    if type_data['init']:
        type_data['init'](obj, params)
    
    return obj


def compute_offsets(obj, sprite_w, sprite_h, hitbox_w, hitbox_h, anchor_type):
    """
    Вычисляет смещения хитбокса и спрайта относительно (x, y).
    Вызывается при инициализации или при смене спрайта.
    """
    obj['sprite_w'] = sprite_w
    obj['sprite_h'] = sprite_h
    obj['w'] = hitbox_w
    obj['h'] = hitbox_h
    obj['anchor_type'] = anchor_type
    
    if anchor_type == 'ground':
        # x,y = середина низа хитбокса
        obj['hitbox_offset_x'] = -hitbox_w / 2.0
        obj['hitbox_offset_y'] = -hitbox_h
        obj['sprite_offset_x'] = -sprite_w / 2.0
        obj['sprite_offset_y'] = -sprite_h
        
    elif anchor_type == 'center':
        # x,y = центр спрайта и хитбокса
        obj['hitbox_offset_x'] = -hitbox_w / 2.0
        obj['hitbox_offset_y'] = -hitbox_h / 2.0
        obj['sprite_offset_x'] = -sprite_w / 2.0
        obj['sprite_offset_y'] = -sprite_h / 2.0


def behave(obj, input_data, ctx):
    """Вызывает функцию behave для данного типа объекта."""
    type_data = OBJECT_TYPES.get(obj['type'])
    if type_data and type_data['behave']:
        type_data['behave'](obj, input_data, ctx)


def transform(obj):
    """Вызывает функцию transform для данного типа объекта."""
    type_data = OBJECT_TYPES.get(obj['type'])
    if type_data and type_data['transform']:
        type_data['transform'](obj)


def get_sprite(obj):
    """Вызывает функцию get_sprite для данного типа объекта."""
    type_data = OBJECT_TYPES.get(obj['type'])
    if type_data and type_data['get_sprite']:
        return type_data['get_sprite'](obj)
    return None


# Для обратной совместимости со старым кодом
TYPE_TO_MOD = {}
ALL = []


def _build_type_to_mod():
    """Заполняет TYPE_TO_MOD из зарегистрированных типов."""
    global TYPE_TO_MOD
    TYPE_TO_MOD = {}
    for name, data in OBJECT_TYPES.items():
        # Создаем псевдо-модуль для совместимости
        class PseudoMod:
            NAME = name
            HITBOX = data['hitbox']
            ANIMS = {}
            ATLAS = []
            DEFAULT = 'idle'
            FALLBACK = ''
            
            @staticmethod
            def update(o, ctx):
                behave(o, {'pressed': [], 'held': {}}, ctx)
            
            @staticmethod
            def anim_state(o):
                return o.get('state', 'idle')
        
        TYPE_TO_MOD[name] = PseudoMod()


def frame(mod, state_name, gtime, have_func):
    """Обратная совместимость: возвращает имя кадра анимации."""
    # Эта функция используется в старом main.py
    # Для новой архитектуры не нужна, но оставлена для совместимости
    if hasattr(mod, 'ANIMS') and state_name in mod.ANIMS:
        anim_data = mod.ANIMS[state_name]
        sequences = anim_data[0]
        speed = anim_data[1] if len(anim_data) > 1 else 1
        seq = sequences[0]
        frame_idx = (gtime // speed) % len(seq)
        return seq[frame_idx]
    return getattr(mod, 'FALLBACK', '')