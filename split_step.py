#!/usr/bin/env python3
# split_step.py — нарезка step.bmp (96×16) на 5 уникальных тайлов

import os
import sys
from PIL import Image

def split_step_tiles(input_path, output_dir='sprites', tile_size=16):
    """
    Нарезает step.bmp (96×16) на тайлы.
    
    Структура (6 тайлов по 16 пикселей):
    [0] [1] [2] [3] [4] [5]
    
    Результат:
    - step_00.bmp — левый крайний (позиция 0)
    - step_01.bmp — левый внутренний (позиция 1)
    - step_center.bmp — центральный (позиции 2, 3 — одинаковые)
    - step_04.bmp — правый внутренний (позиция 4)
    - step_05.bmp — правый крайний (позиция 5)
    """
    # Открываем изображение
    img = Image.open(input_path)
    width, height = img.size
    
    print(f"📐 Размер изображения: {width}×{height}")
    print(f"📏 Размер тайла: {tile_size}×{tile_size}")
    
    # Проверяем размеры
    if height != tile_size:
        print(f"⚠️  Высота {height} не равна размеру тайла {tile_size}")
        tile_height = height
    else:
        tile_height = tile_size
    
    # Количество тайлов по горизонтали
    cols = width // tile_size
    print(f"📊 Всего тайлов: {cols}")
    
    # Создаём выходную директорию
    os.makedirs(output_dir, exist_ok=True)
    
    tiles_info = []
    unique_tiles = {}
    
    # Проходим по всем тайлам слева направо
    for col in range(cols):
        x = col * tile_size
        y = 0
        
        # Вырезаем тайл
        tile = img.crop((x, y, x + tile_size, y + tile_height))
        
        # Определяем имя файла в зависимости от позиции
        if col == 0:
            name = 'step_00.bmp'
            desc = "Левый крайний"
        elif col == 1:
            name = 'step_01.bmp'
            desc = "Левый внутренний"
        elif col == 2:
            name = 'step_center.bmp'
            desc = "Центральный (эталон)"
        elif col == 3:
            # Тайл 3 такой же как тайл 2 (центральный)
            name = 'step_center.bmp'
            desc = "Центральный (дубликат)"
            # Проверяем, отличается ли от центрального
            # Для этого сравниваем с уже сохранённым
            if 'step_center.bmp' in unique_tiles:
                # Проверяем, идентичны ли тайлы
                center_tile = unique_tiles['step_center.bmp']
                if list(tile.getdata()) == list(center_tile.getdata()):
                    print(f"⏭️  Тайл {col} идентичен step_center.bmp, пропускаем")
                else:
                    print(f"⚠️  Тайл {col} отличается от step_center.bmp!")
                    # Сохраняем как отдельный
                    name = f'step_{col:02d}.bmp'
                    desc = f"Центральный вариант {col}"
            else:
                # Если ещё нет центрального, сохраняем этот как эталон
                name = 'step_center.bmp'
                desc = "Центральный (эталон)"
        elif col == 4:
            name = 'step_04.bmp'
            desc = "Правый внутренний"
        elif col == 5:
            name = 'step_05.bmp'
            desc = "Правый крайний"
        else:
            name = f'step_{col:02d}.bmp'
            desc = f"Тайл {col}"
        
        # Сохраняем тайл (если ещё не сохраняли)
        if name not in unique_tiles or col in (0, 1, 4, 5):
            output_path = os.path.join(output_dir, name)
            tile.save(output_path, 'BMP')
            unique_tiles[name] = tile
            print(f"✅ {name} ({tile.size[0]}×{tile.size[1]}) — {desc}")
            tiles_info.append((name, desc, f"позиция {col}"))
        else:
            print(f"⏭️  Пропуск тайла {col} (уже сохранён как {name})")
    
    print(f"\n✨ Сохранено {len(tiles_info)} уникальных тайлов в {output_dir}/")
    
    # Выводим информацию
    print("\n" + "="*60)
    print("📝 Результат нарезки:")
    print("="*60)
    print("\n| Тайл | Описание | Позиция |")
    print("|------|----------|---------|")
    for name, desc, pos in tiles_info:
        print(f"| {name} | {desc} | {pos} |")
    
    print("\n📋 Визуальная схема:")
    print("```")
    print("step.bmp (96×16)")
    print("┌──────┬──────┬──────┬──────┬──────┬──────┐")
    print("│  0   │  1   │  2   │  3   │  4   │  5   │")
    print("└──────┴──────┴──────┴──────┴──────┴──────┘")
    print("   ↓      ↓      ↓      ↓      ↓      ↓")
    
    # Показываем, какие тайлы сохраняются
    names = ['step_00', 'step_01', 'step_center', 'step_center', 'step_04', 'step_05']
    print("   " + "     ".join(names))
    print("   ↓      ↓      ↓      ↓      ↓      ↓")
    descs = ['левый', 'левый', 'центр', 'центр', 'правый', 'правый']
    print("   " + "     ".join(descs))
    print("```")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Нарезка step.bmp (96×16) на тайлы'
    )
    
    parser.add_argument(
        'input',
        default='assets/sheets/step.bmp',
        nargs='?',
        help='Путь к step.bmp (по умолчанию: assets/sheets/step.bmp)'
    )
    
    parser.add_argument(
        '-o', '--output',
        default='assets/sprites',
        help='Директория для сохранения тайлов (по умолчанию: assets/sprites)'
    )
    
    parser.add_argument(
        '-s', '--size',
        type=int,
        default=16,
        help='Размер тайла (по умолчанию: 16)'
    )
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"❌ Файл не найден: {args.input}")
        sys.exit(1)
    
    split_step_tiles(args.input, args.output, args.size)

if __name__ == '__main__':
    main()
