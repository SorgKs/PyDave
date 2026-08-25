#!/usr/bin/env python3
# process_doors.py — обрезает и дополняет до сетки обе открытые двери
# Запуск: python process_doors.py
import os, struct, sys, math

BASE = os.path.dirname(os.path.abspath(__file__))
SPR = os.path.join(BASE, 'assets', 'sprites')
TS = 16

def read_bmp(path):
    with open(path, 'rb') as f:
        data = f.read()
    offset = struct.unpack('<I', data[10:14])[0]
    w = struct.unpack('<I', data[18:22])[0]
    h = struct.unpack('<I', data[22:26])[0]
    px = [[(0,0,0,255)]*w for _ in range(h)]
    for y in range(h):
        row_data = data[offset + y * ((w*3+3)//4)*4 : offset + (y+1) * ((w*3+3)//4)*4]
        for x in range(w):
            b, g, r = row_data[x*3], row_data[x*3+1], row_data[x*3+2]
            if r == 255 and g == 0 and b == 255:
                px[h-1-y][x] = (0, 0, 0, 0)
            else:
                px[h-1-y][x] = (r, g, b, 255)
    return w, h, px

def write_bmp(path, px, w, h):
    rs = ((w*3+3)//4)*4; ps = rs*h
    hdr = b'BM' + struct.pack('<III', 14+40+ps, 0, 54)
    info = struct.pack('<IiiHHIIiiII', 40, w, h, 1, 24, 0, ps, 2835, 2835, 0, 0)
    pix = bytearray()
    for y in range(h-1, -1, -1):
        row = bytearray()
        for x in range(w):
            r, g, b, a = px[y][x]
            row += bytes([255, 0, 255]) if a < 128 else bytes([b, g, r])
        while len(row) % 4: row += b'\x00'
        pix += row
    open(path, 'wb').write(hdr + info + pix)

def crop_to_content(px, w, h):
    """Находит bounding box непрозрачных пикселей и обрезает."""
    min_x, min_y = w, h
    max_x, max_y = -1, -1
    for y in range(h):
        for x in range(w):
            if px[y][x][3] >= 128:
                if x < min_x: min_x = x
                if y < min_y: min_y = y
                if x > max_x: max_x = x
                if y > max_y: max_y = y
    if max_x < 0:
        print('  ! изображение полностью прозрачное')
        return px, w, h
    new_w = max_x - min_x + 1
    new_h = max_y - min_y + 1
    new_px = [row[min_x:max_x+1] for row in px[min_y:max_y+1]]
    print(f'  обрезка: {w}x{h} -> {new_w}x{new_h}')
    return new_px, new_w, new_h

def pad_to_grid(px, w, h):
    """Дополняет до кратного 16: по центру горизонтально, прижата вниз."""
    target_w = math.ceil(w / TS) * TS
    target_h = math.ceil(h / TS) * TS
    add_w = target_w - w
    add_h = target_h - h
    top_pad = add_h
    left_pad = add_w // 2
    right_pad = add_w - left_pad
    new_px = [[(0, 0, 0, 0)] * target_w for _ in range(target_h)]
    for y in range(h):
        for x in range(w):
            new_px[y + top_pad][x + left_pad] = px[y][x]
    print(f'  дополнение: {w}x{h} -> {target_w}x{target_h} (T:{top_pad} L:{left_pad} R:{right_pad})')
    return new_px, target_w, target_h

def process_door(name):
    in_path = os.path.join(SPR, f'{name}.bmp')
    if not os.path.exists(in_path):
        print(f'! не найден {in_path}')
        return
    print(f'\nОбработка {name}.bmp:')
    w, h, px = read_bmp(in_path)
    print(f'  исходный: {w}x{h}')
    px, w, h = crop_to_content(px, w, h)
    px, w, h = pad_to_grid(px, w, h)
    out_path = os.path.join(SPR, f'{name}_padded.bmp')
    write_bmp(out_path, px, w, h)
    print(f'✓ готово: {out_path} ({w}x{h} = {w//TS}x{h//TS} тайлов)')

if __name__ == '__main__':
    print('Обработка открытых дверей...')
    process_door('door1_open')
    process_door('door2_open')
    print('\nГотово!')
