# engine/objects.py — хелперы объектов (без фабрики)
"""
Фабрика — только anims.create_object.
Здесь: якоря, слои, hitbox/sprite helpers, запись collisions.
"""

import pygame

# Канон якоря в obj: 'ground' / 'center'
# Алиас только на входе хелперов
ANCHOR_GROUND = 'ground'
ANCHOR_CENTER = 'center'
ANCHOR_BOTTOM_CENTER = 'bottom_center'  # алиас → ground

# Слои — целые категории (не битовые маски)
LAYER_NONE = 0
LAYER_PLAYER = 1
LAYER_ENEMY = 2
LAYER_ITEM = 3
LAYER_TRIGGER = 4

# Пара (layer_a, layer_b): детекция пересечения
# Отталкивание — подмножество (см. PUSH_PAIRS)
COLLISION_MATRIX = {
    LAYER_PLAYER: {LAYER_ENEMY, LAYER_ITEM, LAYER_TRIGGER},
    LAYER_ENEMY: {LAYER_PLAYER, LAYER_ENEMY},
    LAYER_ITEM: set(),
    LAYER_TRIGGER: set(),
}

# Константы физики в тайлах/кадр (бывшие пиксельные / TS)
GRAVITY = 0.025
MAX_FALL_SPEED = 0.625
FRICTION_GROUND = 0.8
FRICTION_AIR = 0.95
MIN_SPEED = 0.006


def canon_anchor(anchor_type):
    """Приводит алиас к канону 'ground' / 'center'."""
    if anchor_type == ANCHOR_BOTTOM_CENTER:
        return ANCHOR_GROUND
    return anchor_type


def layers_collide(layer_a, layer_b):
    """True, если пара слоёв должна регистрировать коллизию."""
    targets = COLLISION_MATRIX.get(layer_a, set())
    return layer_b in targets


def layers_push(layer_a, layer_b):
    """True, если pass2 разводит объекты и даёт отскок."""
    if layer_a == LAYER_ENEMY and layer_b == LAYER_ENEMY:
        return True
    pair = {layer_a, layer_b}
    return pair == {LAYER_PLAYER, LAYER_ENEMY}

def get_hitbox_rect(obj, ts=1.0):
    """
    Rect хитбокса.
    Если ts==1 — в тайлах (для физики); иначе умножает на ts (пиксели для render/UI).
    """
    return pygame.Rect(
        int((obj['x'] + obj['hitbox_offset_x']) * ts),
        int((obj['y'] + obj['hitbox_offset_y']) * ts),
        max(1, int(obj['w'] * ts)),
        max(1, int(obj['h'] * ts)),
    )


def sprite_draw_offsets(anchor_type, sprite_w, sprite_h):
    """Оффсет верхнего левого угла кадра относительно (x, y) в тех же единицах, что w/h кадра."""
    anchor = canon_anchor(anchor_type)
    if anchor == ANCHOR_GROUND:
        return -sprite_w / 2.0, -sprite_h
    return -sprite_w / 2.0, -sprite_h / 2.0


def get_sprite_render_pos(obj, cam_x, cam_y, sprite_w, sprite_h, ts):
    """
    Экранная позиция верхнего левого угла спрайта.
    obj x/y — тайлы; sprite_w/h и cam — пиксели; ts — пикселей на тайл.
    """
    ox, oy = sprite_draw_offsets(obj.get('anchor_type', ANCHOR_GROUND), sprite_w, sprite_h)
    # доп. визуальный оффсет объекта (в тайлах → пиксели)
    ox += obj.get('sprite_offset_x', 0.0) * ts
    oy += obj.get('sprite_offset_y', 0.0) * ts
    render_x = obj['x'] * ts + ox - cam_x
    render_y = obj['y'] * ts + oy - cam_y
    return render_x, render_y


def clear_collisions(objects_list):
    """Очищает списки коллизий у всех объектов перед новым кадром."""
    for obj in objects_list:
        obj['collisions'] = []


def add_collision(obj, kind, **payload):
    """
    Пишет факт коллизии; набор полей индивидуален для kind.
    kind: 'floor' | 'ceiling' | 'wall' | 'object' | ...
    """
    entry = {'kind': kind}
    entry.update(payload)
    obj['collisions'].append(entry)
