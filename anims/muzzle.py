"""
anims/muzzle.py — анимация вспышки выстрела у дула.

Логика как в webdave (SparkSFX + SmokeSFX объединены в одну 6-кадровую
анимацию: 3 кадра огня → 3 кадра дыма).
"""

from anims import register_object_type


def sprites_map():
    return {
        'muzzle_0': 'muzzle_0.bmp',
        'muzzle_1': 'muzzle_1.bmp',
        'muzzle_2': 'muzzle_2.bmp',
        'muzzle_3': 'muzzle_3.bmp',
        'muzzle_4': 'muzzle_4.bmp',
        'muzzle_5': 'muzzle_5.bmp',
        'muzzle_6': 'muzzle_6.bmp',
        'muzzle_7': 'muzzle_7.bmp',
        'muzzle_8': 'muzzle_8.bmp',
        'muzzle_9': 'muzzle_9.bmp',
        'muzzle_10': 'muzzle_10.bmp',
        'muzzle_11': 'muzzle_11.bmp',
        'muzzle_12': 'muzzle_12.bmp',
        'muzzle_13': 'muzzle_13.bmp',
    }


register_object_type(
    'muzzle',
    sprites_map_func=sprites_map,
)
