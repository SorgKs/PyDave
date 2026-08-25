#!/usr/bin/env python3
# fix_aim_sprites.py — перенарезает aim_up и aim_down с правильными координатами
# Координаты из player.js проекта webdave
import os, struct, urllib.request, zlib

BASE = os.path.dirname(os.path.abspath(__file__))
SHEET_DIR = os.path.join(BASE, 'assets', 'sheets')
SPR = os.path.join(BASE, 'assets', 'sprites')
os.makedirs(SHEET_DIR, exist_ok=True)
os.makedirs(SPR, exist_ok=True)

URL = 'https://raw.githubusercontent.com/lightest/webdave/master/sprites/dave.png'
SCALE = 1  # Оригинальный размер из атласа (48x64)

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

def cut_from(src, name, x0, y0, fw, fh, W, H, scale=SCALE):
    if x0 < 0 or y0 < 0 or x0 + fw > W or y0 + fh > H:
        print(f'  ! {name} вне атласа'); return False
    sub = [row[x0:x0+fw] for row in src[y0:y0+fh]]
    if scale > 1: sub = [r[::scale] for r in sub[::scale]]
    write_bmp(os.path.join(SPR, name + '.bmp'), sub, len(sub[0]), len(sub))
    print(f'  + {name}: {len(sub[0])}x{len(sub)}')
    return True

# Скачиваем dave.png
path = os.path.join(SHEET_DIR, 'dave.png')
if not os.path.exists(path):
    print('качаю dave.png…')
    urllib.request.urlretrieve(URL, path)

W, H, px = read_png(path)
print(f'dave.png: {W}x{H}\n')

print('Нарезка спрайтов прицеливания (правильные координаты из player.js):')
cut_from(px, 'dave_aimup', 980, 0, 42, 64, W, H)      # 42×64
cut_from(px, 'dave_aimdown', 1064, 0, 48, 64, W, H)   # 48×64

print('\nГотово! Спрайты нарезаны в assets/sprites/')
print('Теперь замени dave.py на исправленную версию выше.')