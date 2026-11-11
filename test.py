#!/usr/bin/env python3
# tile_extractor.py — нарезка level01.png на тайлы 16x16 + секции уровня + тест сетки
# Запуск: python tile_extractor.py
import os, struct, urllib.request, zlib

BASE = os.path.dirname(os.path.abspath(__file__))
SHEET_DIR = os.path.join(BASE, 'assets', 'sheets')
SPR = os.path.join(BASE, 'assets', 'sprites', 'tiles')
SECTIONS_DIR = os.path.join(BASE, 'assets', 'sheets', 'sections')
os.makedirs(SHEET_DIR, exist_ok=True)
os.makedirs(SPR, exist_ok=True)
os.makedirs(SECTIONS_DIR, exist_ok=True)

URL = 'https://raw.githubusercontent.com/lightest/webdave/master/sprites/level01.png'
TS = 16

# ---------- PNG-декодер ----------
def read_png(path):
    d = open(path, 'rb').read()
    assert d[:8] == b'\x89PNG\r\n\x1a\n'
    i = 8; idat = b''; plte = trns = None
    while i < len(d):
        ln = struct.unpack('>I', d[i:i+4])[0]
        typ = d[i+4:i+8]; data = d[i+8:i+8+ln]
        if typ == b'IHDR': w, h, bd, ct, _, _, _ = struct.unpack('>IIBBBBB', data)
        elif typ == b'PLTE': plte = data
        elif typ == b'tRNS': trns = data
        elif typ == b'IDAT': idat += data
        elif typ == b'IEND': break
        i += 12 + ln
    raw = zlib.decompress(idat)
    ch = {0:1, 2:3, 3:1, 4:2, 6:4}[ct]
    stride = w * ch
    out = bytearray(h * stride); pos = 0
    for y in range(h):
        f = raw[pos]; pos += 1
        line = bytearray(raw[pos:pos+stride]); pos += stride
        up = out[(y-1)*stride:y*stride] if y else None
        if f == 1:
            for x in range(ch, stride): line[x] = (line[x]+line[x-ch]) & 255
        elif f == 2 and up:
            for x in range(stride): line[x] = (line[x]+up[x]) & 255
        elif f == 3:
            for x in range(stride):
                a = line[x-ch] if x >= ch else 0; b = up[x] if up else 0
                line[x] = (line[x]+(a+b)//2) & 255
        elif f == 4:
            for x in range(stride):
                a = line[x-ch] if x >= ch else 0; b = up[x] if up else 0
                c = up[x-ch] if (up and x >= ch) else 0
                p = a+b-c; pa, pb, pc = abs(p-a), abs(p-b), abs(p-c)
                line[x] = (line[x]+(a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        out[y*stride:(y+1)*stride] = line
    px = [[(0,0,0,0)]*w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            o = y*stride + x*ch
            if ct == 6: px[y][x] = tuple(out[o:o+4])
            elif ct == 2: px[y][x] = (out[o], out[o+1], out[o+2], 255)
            elif ct == 3:
                idx = out[o]; a = trns[idx] if trns and idx < len(trns) else 255
                px[y][x] = (plte[idx*3], plte[idx*3+1], plte[idx*3+2], a)
            elif ct == 4: px[y][x] = (out[o], out[o], out[o], out[o+1])
            else: px[y][x] = (out[o], out[o], out[o], 255)
    return w, h, px

# ---------- BMP-писатель (magenta ТОЛЬКО для прозрачных) ----------
def write_bmp(path, px, w, h):
    rs = ((w*3+3)//4)*4; ps = rs*h
    hdr = b'BM' + struct.pack('<III', 14+40+ps, 0, 54)
    info = struct.pack('<IiiHHIIiiII', 40, w, h, 1, 24, 0, ps, 2835, 2835, 0, 0)
    pix = bytearray()
    for y in range(h-1, -1, -1):
        row = bytearray()
        for x in range(w):
            r, g, b, a = px[y][x]
            if a < 128:
                row += bytes([255, 0, 255])
            else:
                row += bytes([b, g, r])
        while len(row) % 4: row += b'\x00'
        pix += row
    open(path, 'wb').write(hdr + info + pix)

# ---------- BMP-читатель (для тестовой сетки) ----------
def read_bmp(path):
    with open(path, 'rb') as f:
        data = f.read()
    offset = struct.unpack('<I', data[10:14])[0]
    w = struct.unpack('<I', data[18:22])[0]
    h = struct.unpack('<I', data[22:26])[0]
    px = [[(0,0,0,0)]*w for _ in range(h)]
    for y in range(h):
        row_data = data[offset + y * ((w*3+3)//4)*4 : offset + (y+1) * ((w*3+3)//4)*4]
        for x in range(w):
            b, g, r = row_data[x*3], row_data[x*3+1], row_data[x*3+2]
            if r == 255 and g == 0 and b == 255:
                px[h-1-y][x] = (0, 0, 0, 0)  # прозрачный
            else:
                px[h-1-y][x] = (r, g, b, 255)
    return w, h, px

# ---------- Утилиты ----------
def is_empty(tile):
    """Тайл пустой, если ВСЕ пиксели прозрачные (alpha < 128)."""
    for row in tile:
        for r, g, b, a in row:
            if a >= 128:
                return False
    return True

def tile_hash(tile):
    return tuple(tuple((r, g, b, a) for r, g, b, a in row) for row in tile)

def cut_section(px, x0, y0, w, h, name):
    sub = [row[x0:x0+w] for row in px[y0:y0+h]]
    write_bmp(os.path.join(SECTIONS_DIR, name + '.bmp'), sub, w, h)
    print(f'  + секция {name}: {w}x{h}')

# ---------- Скачивание ----------
lv_png = os.path.join(SHEET_DIR, 'level01.png')
if not os.path.exists(lv_png):
    print('качаю level01.png…')
    urllib.request.urlretrieve(URL, lv_png)

W, H, px = read_png(lv_png)
print(f'level01.png: {W}x{H}')

# ============================================================
# ЧАСТЬ 1: Нарезка на тайлы 16x16 с дедупликацией
# ============================================================
print('\n=== ЧАСТЬ 1: Тайлы 16x16 ===')
W_crop = (W // TS) * TS
H_crop = (H // TS) * TS
print(f'обрезка до {W_crop}x{H_crop} ({W_crop//TS}x{H_crop//TS} тайлов)')

unique_tiles = {}
total = 0
empty = 0

for ty in range(H_crop // TS):
    for tx in range(W_crop // TS):
        x0, y0 = tx * TS, ty * TS
        tile = [row[x0:x0+TS] for row in px[y0:y0+TS]]
        total += 1
        if is_empty(tile):
            empty += 1
            continue
        h = tile_hash(tile)
        if h not in unique_tiles:
            unique_tiles[h] = (tile, tx, ty)

print(f'всего тайлов: {total}')
print(f'пустых (прозрачных): {empty}')
print(f'уникальных: {len(unique_tiles)}')

for i, (h, (tile, tx, ty)) in enumerate(unique_tiles.items()):
    write_bmp(os.path.join(SPR, f'tile_{i:03d}.bmp'), tile, TS, TS)

print(f'сохранено {len(unique_tiles)} тайлов в assets/sprites/tiles/')

# Превью-лист
cols = 16
rows = (len(unique_tiles) + cols - 1) // cols
preview_w = cols * TS
preview_h = rows * TS
preview = [[(255, 0, 255, 255)] * preview_w for _ in range(preview_h)]

for i, (h, (tile, tx, ty)) in enumerate(unique_tiles.items()):
    row_idx = i // cols
    col_idx = i % cols
    for y in range(TS):
        for x in range(TS):
            preview[row_idx * TS + y][col_idx * TS + x] = tile[y][x]

write_bmp(os.path.join(SHEET_DIR, 'tiles_preview.bmp'), preview, preview_w, preview_h)
print(f'превью: assets/sheets/tiles_preview.bmp ({preview_w}x{preview_h})')

# ============================================================
# ЧАСТЬ 2: Нарезка уровня на крупные секции
# ============================================================
print('\n=== ЧАСТЬ 2: Секции уровня ===')
SECT_W, SECT_H = 492, 440
cols_sect = (W + SECT_W - 1) // SECT_W
rows_sect = (H + SECT_H - 1) // SECT_H
print(f'разбиение на {cols_sect}x{rows_sect} секций по {SECT_W}x{SECT_H}')

for ry in range(rows_sect):
    for rx in range(cols_sect):
        x0 = rx * SECT_W
        y0 = ry * SECT_H
        w = min(SECT_W, W - x0)
        h = min(SECT_H, H - y0)
        if w <= 0 or h <= 0: continue
        cut_section(px, x0, y0, w, h, f'sect_{ry:02d}_{rx:02d}')

print(f'всего секций: {cols_sect * rows_sect}')

# ============================================================
# ЧАСТЬ 3: Тестовая сетка 10x10 для тайлов 72 и 73
# ============================================================
print('\n=== ЧАСТЬ 3: Тестовая сетка 10x10 (тайлы 72 и 73) ===')
tile_72_path = os.path.join(SPR, 'tile_072.bmp')
tile_73_path = os.path.join(SPR, 'tile_073.bmp')

if os.path.exists(tile_72_path) and os.path.exists(tile_73_path):
    w1, h1, px1 = read_bmp(tile_72_path)
    w2, h2, px2 = read_bmp(tile_73_path)
    
    grid_w, grid_h = 10, 10
    out_w, out_h = grid_w * 16, grid_h * 16
    out_px = [[(255, 0, 255, 255)] * out_w for _ in range(out_h)]
    
    for row in range(grid_h):
        for col in range(grid_w):
            src_px = px1 if (row + col) % 2 == 0 else px2
            for y in range(16):
                for x in range(16):
                    out_px[row * 16 + y][col * 16 + x] = src_px[y][x]

    grid_path = os.path.join(SHEET_DIR, 'tiles_072_073_grid.bmp')
    write_bmp(grid_path, out_px, out_w, out_h)
    print(f'  + тестовая сетка: {grid_path} ({out_w}x{out_h})')
