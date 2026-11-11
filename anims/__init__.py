#!/usr/bin/env python3
"""
anims — реестр типов и фабрика объектов (dict + функции).
Единственная фабрика: create_object. Каноническая структура dict живёт здесь.
"""

# Реестр: имя типа → метаданные и колбэки
OBJECT_TYPES = {}

# Слои коллизий (категории, не битовые маски)
LAYER_NONE = 0
LAYER_PLAYER = 1
LAYER_ENEMY = 2
LAYER_ITEM = 3
LAYER_TRIGGER = 4


def register_object_type(name, init_func=None, behave_func=None,
                         transform_func=None, sprites_map_func=None,
                         hitbox=None, anchor_type='ground', layer=LAYER_NONE,
                         tags=None, has_gravity=True, has_friction=True):
    """Регистрирует тип объекта в OBJECT_TYPES."""
    OBJECT_TYPES[name] = {
        'init': init_func,
        'behave': behave_func,
        'transform': transform_func,
        'sprites_map': sprites_map_func,
        'hitbox': hitbox or (1.0, 1.0),
        'anchor_type': anchor_type,
        'layer': layer,
        'tags': tags or [],
        'has_gravity': has_gravity,
        'has_friction': has_friction,
    }


def create_object(obj_type, x, y, params=None):
    """
    Фабрика: базовый dict → init(obj, params) → compute_offsets (хитбокс).
    x, y, w, h и скорости — в тайлах.
    """
    if obj_type not in OBJECT_TYPES:
        raise ValueError(f"Не найден тип объекта: {obj_type}")

    type_data = OBJECT_TYPES[obj_type]
    hitbox_w, hitbox_h = type_data['hitbox']
    anchor = _canon_anchor(type_data['anchor_type'])

    obj = {
        'type': obj_type,
        'x': float(x),
        'y': float(y),
        'vx': 0.0,
        'vy': 0.0,
        'w': float(hitbox_w),
        'h': float(hitbox_h),
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
        'tags': list(type_data['tags']),
        'has_gravity': type_data['has_gravity'],
        'has_friction': type_data['has_friction'],
        'flash': 0,
        't': 0,
    }

    if type_data['init']:
        type_data['init'](obj, params)

    # Хитбокс-оффсеты один раз после init
    compute_offsets(obj)
    return obj


def _canon_anchor(anchor_type):
    """Канон: 'ground' / 'center'. Алиас bottom_center → ground."""
    if anchor_type == 'bottom_center':
        return 'ground'
    return anchor_type


def compute_offsets(obj):
    """Считает hitbox_offset_* по w/h и anchor_type (один раз при создании)."""
    w = obj['w']
    h = obj['h']
    anchor = _canon_anchor(obj.get('anchor_type', 'ground'))
    obj['anchor_type'] = anchor

    if anchor == 'ground':
        obj['hitbox_offset_x'] = -w / 2.0
        obj['hitbox_offset_y'] = -h
    elif anchor == 'center':
        obj['hitbox_offset_x'] = -w / 2.0
        obj['hitbox_offset_y'] = -h / 2.0
    else:
        raise ValueError(f"Неизвестный anchor_type: {anchor}")


def behave(obj, keys, map_grid, objects_list=None):
    """Диспетчер behave(obj, keys, map) для типа объекта."""
    type_data = OBJECT_TYPES.get(obj['type'])
    if type_data and type_data['behave']:
        type_data['behave'](obj, keys, map_grid, objects_list)


def transform(obj):
    """
    Диспетчер transform(obj) → ключ спрайта (или None).
    Тип сам чистит collisions / события кадра.
    """
    type_data = OBJECT_TYPES.get(obj['type'])
    if type_data and type_data['transform']:
        return type_data['transform'](obj)
    obj['collisions'] = []
    return None


def collect_sprites_maps():
    """Объединяет sprites_map() всех типов: ключ → имя файла."""
    result = {}
    for _name, data in OBJECT_TYPES.items():
        fn = data.get('sprites_map')
        if not fn:
            continue
        for key, filename in fn().items():
            if key not in result:
                result[key] = filename
    return result
