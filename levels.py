# levels.py — парсинг объектов уровня (враги, двери, предметы)
import random

TS = 16

def parse_objects(map_lines):
    """Парсит только игровые объекты из карты, не трогая физику."""
    rows = len(map_lines)
    cols = max(len(r) for r in map_lines)
    
    spikes, torches, gems, hearts, skulls = [], [], [], [], []
    enemies, doors_decor = [], []
    door, key_pos, spawn_pos = None, None, (3 * TS, 11 * TS)
    
    print("\n" + "="*70)
    print("🗺️  НАЧАЛО ПАРСИНГА ОБЪЕКТОВ УРОВНЯ")
    print("="*70)
    
    for y, row in enumerate(map_lines):
        for x, ch in enumerate(row.ljust(cols, '.')):
            px, py = x * TS, y * TS
            
            if ch == '^':
                spikes.append({'x': px, 'y': py})
            elif ch == 'T':
                torches.append({'x': px, 'y': py, 'seed': random.random() * 9})
            elif ch == 'o':
                gems.append({'x': px, 'y': py, 'taken': False, 'seed': random.random() * 9})
            elif ch == 'H':
                hearts.append({'x': px, 'y': py, 'taken': False})
            elif ch == 'k':
                skulls.append((px, py))
            elif ch == 'D':
                door = {'x': px, 'y': py - TS, 'open': 0.0}
            elif ch == 'd':
                doors_decor.append((px, py - TS))
            elif ch == 'K':
                key_pos = (px, py)
            elif ch == 'S':
                spawn_pos = (px, py - 48)
            elif ch == 'Z':
                new_enemy = {
                    'type': 'z', 'x': px + 2.0, 'y': py + 1.0,
                    'w': 16, 'h': 36, 'vx': 0.4, 'vy': 0.0,
                    'hp': 2, 'face': 1, 'flash': 0,
                    't': random.random() * 99, 'onG': False,
                }
                print(f"[🧟 ВРАГ СОЗДАН] Символ: 'Z' | Тайл: ({x}, {y}) | Пиксели: ({px}, {py})")
                print(f"  ↳ Исходные параметры: {new_enemy}")
                enemies.append(new_enemy)
            elif ch == 'G':
                enemies.append({
                    'type': 'g', 'x': px, 'y': py,
                    'w': 12, 'h': 13, 'vx': 0.0, 'vy': 0.0,
                    'flash': 0, 'face': 1, 't': random.random() * 9, 'onG': False,
                })
                
    print("-" * 70)
    print(f"📊 ИТОГО ВРАГОВ НА КАРТЕ: {len(enemies)}")
    for idx, e in enumerate(enemies):
        print(f"  {idx+1}. Тип: '{e['type']}', X: {e['x']:.1f}, Y: {e['y']:.1f}, W: {e['w']}, H: {e['h']}")
    print("=" * 70 + "\n")
                
    return {
        'spikes': spikes,
        'torches': torches,
        'gems': gems,
        'hearts': hearts,
        'skulls': skulls,
        'enemies': enemies,
        'doors_decor': doors_decor,
        'door': door,
        'key_pos': key_pos,
        'spawn_pos': spawn_pos,
        'total_gems': len(gems),
    }