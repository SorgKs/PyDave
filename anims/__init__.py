#!/usr/bin/env python3
# anims/__init__.py — общий модуль анимаций
import anims.dave

# Маппинг типов врагов к модулям
TYPE_TO_MOD = {
    'z': None,  # zombie
    'g': None,  # goblin
    'b': None,  # bat
}

# Список всех доступных модулей анимаций
ALL = [anims.dave]

# Безопасный импорт зомби
try:
    import anims.zombie
    TYPE_TO_MOD['z'] = anims.zombie
    ALL.append(anims.zombie)
except ImportError as e:
    print(f"⚠️ Не удалось импортировать anims.zombie: {e}")

# Безопасный импорт гоблина
try:
    import anims.goblin
    TYPE_TO_MOD['g'] = anims.goblin
    TYPE_TO_MOD['b'] = anims.goblin
    ALL.append(anims.goblin)
except ImportError as e:
    print(f"⚠️ Не удалось импортировать anims.goblin: {e}")


def frame(mod, state, t, have):
    """Возвращает имя спрайта для текущего кадра анимации."""
    if state not in mod.ANIMS:
        state = getattr(mod, 'DEFAULT', 'idle')

    anim_data = mod.ANIMS[state]
    sequences = anim_data[0]
    speed = anim_data[1]

    seq = sequences[0]
    frame_idx = (t // speed) % len(seq)
    frame_name = seq[frame_idx]

    if not have(frame_name):
        return getattr(mod, 'FALLBACK', seq[0])

    return frame_name


def fix_sizes(enemies):
    """Добавляет врагам размеры спрайта и физические переменные."""
    for e in enemies:
        mod = TYPE_TO_MOD.get(e['type'])
        if not mod:
            raise ValueError(
                f"❌ КРИТИЧЕСКАЯ ОШИБКА: Не найден модуль анимации для врага типа '{e['type']}'!\n"
                f"Проверь наличие файла anims/{e['type']}.py и его импорт в anims/__init__.py"
            )

        # Размеры хитбокса для коллизий
        e['w'], e['h'] = mod.HITBOX

        # Визуальные размеры спрайта (из первого кадра ATLAS: name, x, y, w, h)
        if mod.ATLAS:
            e['sprite_w'] = mod.ATLAS[0][3]
            e['sprite_h'] = mod.ATLAS[0][4]
        else:
            e['sprite_w'] = e['w']
            e['sprite_h'] = e['h']

        # Физические переменные (гарантируем наличие)
        e.setdefault('vx', 0.0)
        e.setdefault('vy', 0.0)
        e.setdefault('onG', False)
        e.setdefault('face', -1)
        e.setdefault('drop', 0)
        e.setdefault('t', 0)
        e.setdefault('flash', 0)
        e.setdefault('hp', 2)