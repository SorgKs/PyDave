# assets.py — загрузка тайлов и спрайтов объектов
import os
import sys

try:
    import pygame
except ImportError:
    sys.exit('нужен pygame:  pip install pygame')

from config import BG_TRANSPARENT, MUSIC_VOL

BASE = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE, 'assets')

SOUNDS = (
    'jump', 'shoot', 'hit', 'kill', 'gem', 'key',
    'heart', 'hurt', 'die', 'land', 'door',
    'reload', 'noAmmo',
)
MUSIC_NAME = 'music'

STATIC_TILES = (
    'heart', 'door_closed',  # door_open отсутствует
)


def _check_assets():
    for d in ('sprites', 'sounds'):
        if not os.path.isdir(os.path.join(ASSETS_DIR, d)):
            sys.exit('Папка assets не найдена. Сначала выполните:  python gen_assets.py')


def load_image(name, colorkey=False, scale=1):
    """
    name — имя файла (с расширением) или stem.
    colorkey: прозрачный только BG_TRANSPARENT (magenta);
              чёрный (0,0,0) и любые другие цвета непрозрачны.
    scale: целочисленный масштаб (файлы на диске не меняются).
    """
    if not name.endswith(('.bmp', '.png')):
        name = name + '.bmp'
    path = os.path.join(ASSETS_DIR, 'sprites', name)
    # convert() до ключа — корректный map_rgb для display-формата
    s = pygame.image.load(path).convert()
    if scale != 1:
        w, h = s.get_size()
        s = pygame.transform.scale(s, (w * scale, h * scale))
    if colorkey:
        s = _magenta_key_only(s)
    return s


def _magenta_key_only(surf):
    """
    Делает прозрачным только точный BG_TRANSPARENT.
    Чёрные пиксели остаются чёрными (alpha=255).
    """
    out = surf.convert_alpha()
    rgb = pygame.surfarray.pixels3d(out)
    alpha = pygame.surfarray.pixels_alpha(out)
    r, g, b = BG_TRANSPARENT
    mask = (rgb[:, :, 0] == r) & (rgb[:, :, 1] == g) & (rgb[:, :, 2] == b)
    alpha[:, :] = 255
    alpha[mask] = 0
    del rgb, alpha
    # colorkey не ставим — иначе SDL может снова затронуть чёрный
    return out


def load_sound(name):
    path = os.path.join(ASSETS_DIR, 'sounds', name)
    try:
        return pygame.mixer.Sound(path)
    except Exception:
        return None


def load_tiles():
    """Тайлы уровня: spike, heart, ammo, door."""
    imgs = {}
    for n in STATIC_TILES:
        imgs[n] = load_image(n + '.bmp', colorkey=True)
    return imgs


def load_object_sprites():
    """
    Агрегирует sprites_map() всех типов anims → ключ → surface.
    Типы должны быть уже зарегистрированы (import anims.*).
    """
    from anims import collect_sprites_maps
    imgs = {}
    for key, filename in collect_sprites_maps().items():
        imgs[key] = load_image(filename, colorkey=True)
    return imgs


def load_all_sprites():
    """Тайлы + спрайты объектов из anims.sprites_map."""
    imgs = load_tiles()
    imgs.update(load_object_sprites())
    return imgs


def make_white_variant(surface):
    """«Ослепляющая» копия спрайта (урон). Сохраняет alpha (чёрный не теряется)."""
    w = surface.copy()
    w.fill((0, 0, 0), special_flags=pygame.BLEND_RGB_MULT)
    w.fill((255, 255, 255), special_flags=pygame.BLEND_RGB_ADD)
    return w


def load_all_sounds():
    sfx = {}
    for n in SOUNDS:
        sfx[n] = load_sound(n + '.wav')
    music = load_sound(MUSIC_NAME + '.wav')
    if music:
        music.set_volume(MUSIC_VOL)
        music.play(-1)
    return sfx, music
