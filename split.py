#!/usr/bin/env python3
# split_all_atlas.py — нарезка всех спрайтов из webdave.png по ATLAS из anims/*.py

import os
from PIL import Image
from config import BG_TRANSPARENT

# Импортируем все модули анимаций
import anims.dave
import anims.zombie
import anims.ghost
import anims.skull

MODULES = [anims.dave, anims.zombie, anims.ghost, anims.skull]

# Путь к основному атласу (dave.png из webdave)
INPUT_PATH = "assets/sheets/dave.png"
OUTPUT_DIR = "assets/sprites"
COLORKEY = BG_TRANSPARENT

def main():
    # Проверяем наличие атласа
    if not os.path.exists(INPUT_PATH):
        print(f"❌ Файл {INPUT_PATH} не найден!")
        print("   Убедитесь, что webdave.png скачан в assets/sheets/")
        print("   Если у вас другой атлас, измените INPUT_PATH.")
        return

    # Открываем изображение
    img = Image.open(INPUT_PATH)
    print(f"📂 Загружен {INPUT_PATH} ({img.width}×{img.height})")

    # Создаём папку для сохранения
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    total = 0
    for mod in MODULES:
        if not hasattr(mod, 'ATLAS'):
            print(f"⚠️ Модуль {mod.__name__} не имеет ATLAS, пропускаем.")
            continue
        if not mod.ATLAS:
            print(f"⚠️ Модуль {mod.__name__} имеет пустой ATLAS, пропускаем.")
            continue

        print(f"\n🔹 Обработка {mod.__name__}")
        for name, x, y, w, h in mod.ATLAS:
            # Вырезаем кадр
            frame = img.crop((x, y, x + w, y + h))

            # Создаём фон с colorkey
            bg = Image.new("RGB", (w, h), COLORKEY)
            bg.paste(frame, (0, 0), frame)

            # Сохраняем как BMP
            out_path = os.path.join(OUTPUT_DIR, f"{name}.bmp")
            bg.save(out_path, "BMP")
            print(f"  ✅ {name}.bmp ({w}×{h}) сохранён (x={x}, y={y})")
            total += 1

    print(f"\n✨ Готово! Сохранено {total} спрайтов в {OUTPUT_DIR}/")

if __name__ == "__main__":
    main()
