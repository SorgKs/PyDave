#!/usr/bin/env python3
# split_zombie.py — нарезка зомби из dave.png (как split_dave / webdave zombie.js)
import os
from PIL import Image

BASE = os.path.dirname(os.path.abspath(__file__))
SHEET = os.path.join(BASE, 'assets', 'sheets', 'dave.png')
OUT = os.path.join(BASE, 'assets', 'sprites')
MAGENTA = (255, 0, 255)

# origins из monsters/zombie.js (spriteImg = dave.png)
ATLAS = [
    ('zombie_walk1', 0, 566, 50, 80),
    ('zombie_walk2', 50, 566, 50, 80),
    ('zombie_walk3', 100, 566, 50, 80),
    ('zombie_walk4', 150, 566, 50, 80),
    ('zombie_atk1', 200, 566, 98, 80),
    ('zombie_atk2', 298, 566, 98, 80),
    ('zombie_atk3', 396, 566, 98, 80),
    ('zombie_fall1', 988, 566, 50, 80),
    ('zombie_fall2', 1038, 566, 50, 80),
]


def main():
    im = Image.open(SHEET).convert('RGBA')
    print(f'dave.png: {im.size}')
    os.makedirs(OUT, exist_ok=True)
    for name, x, y, w, h in ATLAS:
        crop = im.crop((x, y, x + w, y + h))
        out = Image.new('RGB', (w, h), MAGENTA)
        sp, dp = crop.load(), out.load()
        for j in range(h):
            for i in range(w):
                r, g, b, a = sp[i, j]
                # прозрачный только alpha; чёрный сохраняем
                dp[i, j] = MAGENTA if a < 128 else (r, g, b)
        path = os.path.join(OUT, name + '.bmp')
        out.save(path, 'BMP')
        print(f'  + {name}.bmp ({w}x{h})')
    print(f'Готово → {OUT}/')


if __name__ == '__main__':
    main()
