#!/usr/bin/env python3
# trim_png_to_bmp_alpha.py — обрезка PNG и сохранение в BMP с альфа-каналом

import os
import sys
from PIL import Image

def trim_image(image):
    bbox = image.getbbox()
    if bbox:
        return image.crop(bbox)
    return image

def process_file(input_path, output_dir=None):
    if not input_path.lower().endswith('.png'):
        print(f"⚠️  Пропуск: {input_path}")
        return False
    
    try:
        img = Image.open(input_path)
        
        # Конвертируем в RGBA если нужно
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Обрезаем
        trimmed = trim_image(img)
        
        # Сохраняем как BMP с альфа-каналом (32-bit)
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, base_name + '.bmp')
        else:
            output_path = os.path.join(os.path.dirname(input_path), base_name + '.bmp')
        
        # BMP с альфа-каналом (BGRA)
        trimmed.save(output_path, 'BMP')
        print(f"✅ {input_path} -> {output_path}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

# Использование: python trim_png_to_bmp_alpha.py sprite.png
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Использование: python trim_png_to_bmp_alpha.py <png_file> [output_dir]")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    process_file(input_path, output_dir)
