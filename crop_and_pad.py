#!/usr/bin/env python3
# crop_and_pad.py — обрезает PNG до bounding box непрозрачных пикселей,
# затем дополняет до сетки 16x16 (по центру горизонтально, прижата вниз)
# и сохраняет как BMP.
# Запуск: python crop_and_pad.py [вход.png] [выход.bmp]
# По умолчанию: door1.png -> door1.bmp
import os, struct, sys, zlib, math

BASE = os.path.dirname(os.path.abspath(__file__))
TS = 16

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
    print(f'  обрезка до контента: {w}x{h} -> {new_w}x{new_h} (x:{min_x}..{max_x}, y:{min_y}..{max_y})')
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
    print(f'  дополнение до сетки: {w}x{h} -> {target_w}x{target_h} (T:{top_pad} B:0 L:{left_pad} R:{right_pad})')
    return new_px, target_w, target_h

def find_input(name):
    candidates = [
        name,
        os.path.join(BASE, name),
        os.path.join(BASE, 'assets', 'sheets', name),
        os.path.join(BASE, 'assets', 'sprites', name),
        os.path.join(BASE, 'assets', 'sprites', 'tiles', name),
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None

if __name__ == '__main__':
    in_name = sys.argv[1] if len(sys.argv) > 1 else 'door1.png'
    out_name = sys.argv[2] if len(sys.argv) > 2 else in_name.rsplit('.', 1)[0] + '.bmp'
    in_path = find_input(in_name)
    if not in_path:
        print(f'! не найден {in_name}')
        sys.exit(1)
    print(f'вход: {in_path}')
    w, h, px = read_png(in_path)
    print(f'исходный размер: {w}x{h}')
    px, w, h = crop_to_content(px, w, h)
    px, w, h = pad_to_grid(px, w, h)
    out_dir = os.path.dirname(in_path) or os.path.join(BASE, 'assets', 'sheets')
    out_path = os.path.join(out_dir, out_name)
    write_bmp(out_path, px, w, h)
    print(f'✓ готово: {out_path} ({w}x{h} = {w//TS}x{h//TS} тайлов)')
