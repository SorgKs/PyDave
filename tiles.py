# tiles.py — загрузка тайлов уровня (пол, обои, воздух, стены, лестница)
import os
import pygame
from config import TS, BG_TRANSPARENT
from assets import ASSETS_DIR, load_image

def load_tiles():
    tiles = {}
    print("🔄 Загрузка тайлов...")

    # 1. Стены, платформы, двери (заглушки, если нет)
    base_names = ('tile_wall', 'tile_wall_top', 'tile_plat',
                  'brick0', 'brick1', 'brick2',
                  'brick_top0', 'brick_top1', 'brick_top2',
                  'door_closed', 'door_open', 'door_orig')
    for name in base_names:
        try:
            tiles[name] = load_image(name + '.bmp', colorkey=True)
        except FileNotFoundError:
            tiles[name] = pygame.Surface((TS, TS))
            tiles[name].fill((80, 60, 40))
            print(f"⚠️ Заглушка для {name}")

    # 2. Лестница (step_00 … step_04)
    for name in ('step_00', 'step_01', 'step_02', 'step_03', 'step_04'):
        path = os.path.join(ASSETS_DIR, 'sprites', 'tiles', name + '.bmp')
        if os.path.exists(path):
            try:
                surf = pygame.image.load(path).convert()
                surf.set_colorkey(BG_TRANSPARENT)
                tiles[name] = surf
                print(f"✅ {name} загружен")
            except Exception:
                tiles[name] = pygame.Surface((TS, TS))
                tiles[name].fill((120, 100, 80))
                pygame.draw.rect(tiles[name], (100, 80, 60), (0, TS//2, TS, TS//2))
        else:
            tiles[name] = pygame.Surface((TS, TS))
            tiles[name].fill((120, 100, 80))
            pygame.draw.rect(tiles[name], (100, 80, 60), (0, TS//2, TS, TS//2))

    # 3. Пол (один тайл) – ищем floor.bmp или floor_title.bmp
    floor_path = os.path.join(ASSETS_DIR, 'sprites', 'tiles', 'floor.bmp')
    if not os.path.exists(floor_path):
        floor_path = os.path.join(ASSETS_DIR, 'sprites', 'tiles', 'floor_title.bmp')
    if os.path.exists(floor_path):
        try:
            surf = pygame.image.load(floor_path).convert()
            surf.set_colorkey(BG_TRANSPARENT)
            tiles['floor'] = surf
            print(f"✅ floor загружен из {os.path.basename(floor_path)}")
        except Exception as e:
            print(f"⚠️ Ошибка загрузки пола: {e}")
            surf = pygame.Surface((TS, TS))
            surf.fill((180, 130, 80))
            tiles['floor'] = surf
    else:
        print("⚠️ floor.bmp/floor_title.bmp не найден, создаём заглушку")
        surf = pygame.Surface((TS, TS))
        surf.fill((180, 130, 80))
        tiles['floor'] = surf

    # 4. Обои (wallpaper_a, wallpaper_b)
    wp_a_path = os.path.join(ASSETS_DIR, 'sprites', 'tiles', 'wallpaper_a.bmp')
    wp_b_path = os.path.join(ASSETS_DIR, 'sprites', 'tiles', 'wallpaper_b.bmp')

    def load_wallpaper(name, path):
        if os.path.exists(path):
            try:
                surf = pygame.image.load(path).convert()
                surf.set_colorkey(BG_TRANSPARENT)
                print(f"✅ {name} загружен")
                return surf
            except:
                pass
        surf = pygame.Surface((TS, TS))
        if name == 'wallpaper_a':
            surf.fill((220, 200, 180))
        else:
            surf.fill((200, 180, 160))
        print(f"⚠️ Заглушка для {name}")
        return surf

    tiles['wallpaper_a'] = load_wallpaper('wallpaper_a', wp_a_path)
    tiles['wallpaper_b'] = load_wallpaper('wallpaper_b', wp_b_path)

    # 5. Воздух (air)
    air_path = os.path.join(ASSETS_DIR, 'sprites', 'tiles', 'air.bmp')
    if os.path.exists(air_path):
        try:
            surf = pygame.image.load(air_path).convert()
            surf.set_colorkey(BG_TRANSPARENT)
            tiles['air'] = surf
            print("✅ air загружен")
        except:
            tiles['air'] = pygame.Surface((TS, TS))
            tiles['air'].fill((30, 30, 30))
    else:
        tiles['air'] = pygame.Surface((TS, TS))
        tiles['air'].fill((30, 30, 30))
        print("⚠️ Заглушка для air")

    # 6. Для совместимости: stair_*
    for i in range(12):
        name = f'stair_{i:02d}'
        try:
            tiles[name] = load_image(name + '.bmp', colorkey=True)
        except:
            pass

    print(f"📦 Загружено тайлов: {len(tiles)}")
    return tiles
