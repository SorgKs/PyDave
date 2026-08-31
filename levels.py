# levels.py — парсинг уровня: символы → create_object (канонические типы)
import random

from anims import create_object

# Символ карты → канонический тип (только объекты)
_CHAR_TO_TYPE = {
    'Z': 'zombie',
    'G': 'goblin',
    'o': 'item_gem',
    'k': 'skull',
}


def parse_objects(map_lines):
    """
    Парсит карту: сразу create_object + init.
    Координаты объектов — в тайлах.
    Декор (шипы, факелы, двери) — отдельные списки в тайлах.
    """
    # Регистрация типов до create_object
    import anims.dave  # noqa: F401
    import anims.zombie  # noqa: F401
    import anims.goblin  # noqa: F401
    # skull/item_gem: спрайты не извлечены — отключены

    cols = max(len(r) for r in map_lines)

    spikes, torches, hearts = [], [], []
    doors_decor = []
    door, key_pos = None, None
    spawn_pos = (3.0, 11.0)
    objects = []
    player = None

    for y, row in enumerate(map_lines):
        for x, ch in enumerate(row.ljust(cols, '.')):
            tx, ty = float(x), float(y)

            if ch == '^':
                spikes.append({'x': tx, 'y': ty})
            elif ch == 'T':
                torches.append({'x': tx, 'y': ty, 'seed': random.random() * 9})
            elif ch == 'H':
                hearts.append({'x': tx, 'y': ty, 'taken': False})
            elif ch == 'D':
                door = {'x': tx, 'y': ty - 1.0, 'open': 0.0}
            elif ch == 'd':
                doors_decor.append((tx, ty - 1.0))
            elif ch == 'K':
                key_pos = (tx, ty)
            elif ch == 'S':
                # Ноги на нижней границе клетки спавна
                spawn_pos = (tx + 0.5, ty + 1.0)
            elif ch in _CHAR_TO_TYPE:
                obj_type = _CHAR_TO_TYPE[ch]
                params = None
                ox, oy = tx, ty
                if obj_type == 'zombie':
                    ox, oy = tx + 0.125, ty + 1.0
                    params = {'vx': 0.025, 'hp': 2}
                elif obj_type == 'goblin':
                    ox, oy = tx + 0.5, ty + 1.0
                elif obj_type == 'item_gem':
                    ox, oy = tx + 0.5, ty + 0.5
                    params = {'seed': random.random() * 9}
                elif obj_type == 'skull':
                    ox, oy = tx + 0.5, ty + 0.5

                obj = create_object(obj_type, ox, oy, params)
                objects.append(obj)

    player = create_object('dave', spawn_pos[0], spawn_pos[1])
    objects.insert(0, player)

    return {
        'objects': objects,
        'player': player,
        'spikes': spikes,
        'torches': torches,
        'hearts': hearts,
        'doors_decor': doors_decor,
        'door': door,
        'key_pos': key_pos,
        'spawn_pos': spawn_pos,
    }
