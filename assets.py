# assets.py — загрузка спрайтов/звуков
import os, sys
try:
    import pygame
except ImportError:
    sys.exit('нужен pygame:  pip install pygame')

from config import BG_TRANSPARENT, MUSIC_VOL

BASE = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE, 'assets')

# Только статические спрайты (не анимации)
# Анимации загружаются через ATLAS в anims/*.py
SPRITES = (
    # Dave (базовые)
    'dave_idle', 'dave_walk1', 'dave_walk2', 'dave_walk3', 'dave_walk4',
    'dave_jump', 'dave_fall', 'dave_shoot', 'dave_shoot2',
    'dave_aimup', 'dave_aimdown',
    'dave_door1', 'dave_door2', 'dave_door3', 'dave_door4',
    # Death (кадры смерти)
    'death_00', 'death_01', 'death_02', 'death_03', 'death_04',
    'death_05', 'death_06', 'death_07', 'death_08', 'death_09',
    'death_10', 'death_11', 'death_12', 'death_13', 'death_14',
    'death_15', 'death_16', 'death_17', 'death_18', 'death_19',
    'death_20', 'death_21', 'death_22', 'death_23', 'death_24',
    'death_25', 'death_26', 'death_27', 'death_28', 'death_29',
    'death_30', 'death_31', 'death_32', 'death_33', 'death_34',
    'death_35', 'death_36', 'death_37', 'death_38', 'death_39',
    # Предметы
    'key', 'gem', 'heart', 'skull',
    # Тайлы (статические)
    'brick0', 'brick1', 'brick2',
    'brick_top0', 'brick_top1', 'brick_top2',
    'slab', 'spike', 'door_closed', 'door_open',
    'tile_wall', 'tile_wall_top', 'tile_plat',
    # Ступени (статические тайлы)
    'stair_00', 'stair_01', 'stair_02', 'stair_03', 'stair_04',
    'stair_05', 'stair_06', 'stair_07', 'stair_08', 'stair_09',
    'stair_10', 'stair_11',
    # Боеприпасы
    'ammo_0', 'ammo_1', 'ammo_2', 'ammo_3', 'ammo_4',
    'ammo_5', 'ammo_6', 'ammo_7', 'ammo_8',
    # Двери
    'door1_closed', 'door1_open', 'door2_closed', 'door2_open',
    # Объекты
    'obj_000', 'obj_001', 'obj_002', 'obj_003', 'obj_004',
    'obj_005', 'obj_006', 'obj_007', 'obj_008', 'obj_009',
    'obj_010', 'obj_011', 'obj_012', 'obj_013', 'obj_014',
    'obj_015', 'obj_016', 'obj_017', 'obj_018', 'obj_019',
    'obj_020', 'obj_021', 'obj_022', 'obj_023', 'obj_024',
    'obj_025', 'obj_026', 'obj_027', 'obj_028', 'obj_029',
)

# Аддитивные спрайты (свечения, фон)
ADDITIVE_SPRITES = (
    'glow_torch', 'glow_ghost', 'glow_key', 'glow_door',
    'glow_moon', 'fog', 'moon', 'sky',
)

SOUNDS = (
    'jump', 'shoot', 'hit', 'kill', 'gem', 'key',
    'heart', 'hurt', 'die', 'land', 'door',
)
MUSIC_NAME = 'music'


def _check_assets():
    for d in ('sprites', 'sounds'):
        if not os.path.isdir(os.path.join(ASSETS_DIR, d)):
            sys.exit('Папка assets не найдена. Сначала выполните:  python gen_assets.py')


def load_image(name, colorkey=False):
    path = os.path.join(ASSETS_DIR, 'sprites', name)
    s = pygame.image.load(path)
    if colorkey:
        s.set_colorkey(BG_TRANSPARENT)
    return s.convert()


def load_sound(name):
    path = os.path.join(ASSETS_DIR, 'sounds', name)
    try:
        return pygame.mixer.Sound(path)
    except Exception:
        return None


def load_all_sprites():
    imgs = {}
    for n in SPRITES:
        try:
            imgs[n] = load_image(n + '.bmp', colorkey=True)
        except FileNotFoundError:
            print(f"⚠️  {n}.bmp не найден")
            continue
    for n in ADDITIVE_SPRITES:
        try:
            imgs[n] = load_image(n + '.bmp', colorkey=False)
        except FileNotFoundError:
            print(f"⚠️  {n}.bmp не найден")
            continue
    return imgs


def make_white_variant(surface):
    """Создаёт "ослепляющую" копию спрайта (для эффекта попадания)."""
    ck = surface.get_colorkey()
    w = surface.copy()
    w.fill((0, 0, 0), special_flags=pygame.BLEND_RGB_MULT)
    w.fill((255, 255, 255), special_flags=pygame.BLEND_RGB_ADD)
    if ck:
        w.set_colorkey(ck)
    return w


def load_all_sounds():
    sfx = {}
    music = None
    for n in SOUNDS:
        sfx[n] = load_sound(n + '.wav')
    music = load_sound(MUSIC_NAME + '.wav')
    if music:
        music.set_volume(MUSIC_VOL)
        music.play(-1)
    return sfx, music
