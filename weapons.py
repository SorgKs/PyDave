#!/usr/bin/env python3
"""weapons.py — характеристики оружия Дейва."""
from config import FPS

# Параметры текущей стрельбы (двустволка)
_SHOOT_RECOIL = 0.1125
_SHOOT_STOP = FPS * 2 // 5   # 0.4 с — пауза после выстрела
_SHOOT_COOL = FPS // 2       # 0.5 с — кулдаун между выстрелами

WEAPONS = {
    'double_barrel': {
        'id': 'double_barrel',
        'max_ammo': 2,
        'damage': 1,
        'recoil': _SHOOT_RECOIL,
        'shoot_cool': _SHOOT_COOL,
        'shoot_stop': _SHOOT_STOP,
        'shoot_anim_speed': 6,
    },
}


def get_weapon(weapon_id):
    """Возвращает описание оружия или двустволку по умолчанию."""
    return WEAPONS.get(weapon_id, WEAPONS['double_barrel'])
