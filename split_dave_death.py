#!/usr/bin/env python3
# split_dave_death.py — все анимации смерти Дейва (webdave Game.js + deaths-of-dave.png)
import os
from PIL import Image

BASE = os.path.dirname(os.path.abspath(__file__))
SHEET_DAVE = os.path.join(BASE, 'assets', 'sheets', 'dave.png')
SHEET_DEATHS = os.path.join(BASE, 'assets', 'sheets', 'deaths-of-dave.png')
OUT = os.path.join(BASE, 'assets', 'sprites')
MAGENTA = (255, 0, 255)

# Game.js initAnimations — playerDeathZombie / playerDeathKnife (dave.png, y=66)
DAVE_DEATH_ATLAS = []
for i in range(5):
    DAVE_DEATH_ATLAS.append(
        ('dave_death_zombie%d' % (i + 1), i * 96, 66, 96, 96))
for i in range(4):
    DAVE_DEATH_ATLAS.append(
        ('dave_death_knife%d' % (i + 1), 480 + i * 96, 66, 96, 96))

# deaths-of-dave.png — сетка 48×48 (240×384 → 5×8 = 40 кадров)
DEATHS_GALLERY_CELL = 48


def _save_frame(crop, path):
    out = Image.new('RGB', crop.size, MAGENTA)
    sp, dp = crop.load(), out.load()
    w, h = crop.size
    for j in range(h):
        for i in range(w):
            r, g, b, a = sp[i, j]
            dp[i, j] = MAGENTA if a < 128 else (r, g, b)
    out.save(path, 'BMP')


def _cut_atlas(im, atlas, label):
    n = 0
    for name, x, y, w, h in atlas:
        crop = im.crop((x, y, x + w, y + h))
        path = os.path.join(OUT, name + '.bmp')
        _save_frame(crop, path)
        print('  + %s.bmp (%dx%d)' % (name, w, h))
        n += 1
    print('%s: %d спрайтов' % (label, n))
    return n


def _cut_deaths_gallery(im):
    w, h = im.size
    cols = w // DEATHS_GALLERY_CELL
    rows = h // DEATHS_GALLERY_CELL
    n = 0
    for row in range(rows):
        for col in range(cols):
            x0 = col * DEATHS_GALLERY_CELL
            y0 = row * DEATHS_GALLERY_CELL
            crop = im.crop((x0, y0, x0 + DEATHS_GALLERY_CELL, y0 + DEATHS_GALLERY_CELL))
            # пропуск пустых ячеек
            if crop.getbbox() is None:
                continue
            name = 'death_%02d' % n
            path = os.path.join(OUT, name + '.bmp')
            _save_frame(crop, path)
            print('  + %s.bmp (%dx%d)' % (name, DEATHS_GALLERY_CELL, DEATHS_GALLERY_CELL))
            n += 1
    print('deaths-of-dave.png: %d спрайтов' % n)
    return n


def main():
    os.makedirs(OUT, exist_ok=True)
    total = 0

    if not os.path.exists(SHEET_DAVE):
        print('нет', SHEET_DAVE)
        return
    im = Image.open(SHEET_DAVE).convert('RGBA')
    print('dave.png: %dx%d' % im.size)
    print('Игровые анимации смерти (Game.js):')
    total += _cut_atlas(im, DAVE_DEATH_ATLAS, 'dave.png')

    if not os.path.exists(SHEET_DEATHS):
        print('нет', SHEET_DEATHS)
    else:
        im2 = Image.open(SHEET_DEATHS).convert('RGBA')
        print('\ndeaths-of-dave.png: %dx%d' % im2.size)
        print('Галерея смертей (48×48):')
        total += _cut_deaths_gallery(im2)

    print('\nГотово → %s/ (%d файлов)' % (OUT, total))


if __name__ == '__main__':
    main()
