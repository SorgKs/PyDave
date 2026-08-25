#!/usr/bin/env python3
# convert.py — нарезка оригинальных спрайтов DD2
import os, struct, urllib.request, zlib, json
import anims

BASE = os.path.dirname(os.path.abspath(__file__))
SHEET_DIR = os.path.join(BASE, 'assets', 'sheets')
SPR = os.path.join(BASE, 'assets', 'sprites')
os.makedirs(SHEET_DIR, exist_ok=True)
URL = 'https://raw.githubusercontent.com/lightest/webdave/master/sprites/dave.png'
ROOT_URL = 'https://raw.githubusercontent.com/lightest/webdave/master/'
RE_URL = 'https://raw.githubusercontent.com/gmegidish/dangerous-dave-re/master/images/'
SCALE = 2

def read_png(path):
    d = open(path, 'rb').read(); assert d[:8] == b'\x89PNG\r\n\x1a\n'
    i = 8; idat = b''; plte = trns = None
    while i < len(d):
        ln = struct.unpack('>I', d[i:i+4])[0]; typ = d[i+4:i+8]; data = d[i+8:i+8+ln]
        if typ == b'IHDR': w, h, bd, ct, _, _, _ = struct.unpack('>IIBBBBB', data)
        elif typ == b'PLTE': plte = data
        elif typ == b'tRNS': trns = data
        elif typ == b'IDAT': idat += data
        elif typ == b'IEND': break
        i += 12 + ln
    raw = zlib.decompress(idat); ch = {0:1, 2:3, 3:1, 4:2, 6:4}[ct]; stride = w*ch
    out = bytearray(h*stride); pos = 0
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
            row += bytes([255, 0, 255]) if a < 128 or (r+g+b) == 0 else bytes([b, g, r])
        while len(row) % 4: row += b'\x00'
        pix += row
    open(path, 'wb').write(hdr + info + pix)

def write_png(path, px, w, h):
    def chunk(t, d):
        return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    raw = b''.join(b'\x00' + bytes(v for p in row for v in p[:3]) for row in px)
    data = (b'\x89PNG\r\n\x1a\n'
            + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(raw, 6))
            + chunk(b'IEND', b''))
    open(path, 'wb').write(data)

def cut_from(src, name, x0, y0, fw, fh, W, H, scale=SCALE):
    if x0 < 0 or y0 < 0 or x0 + fw > W or y0 + fh > H:
        print('  !', name, 'вне атласа'); return False
    sub = [row[x0:x0+fw] for row in src[y0:y0+fh]]
    if scale > 1: sub = [r[::scale] for r in sub[::scale]]
    write_bmp(os.path.join(SPR, name + '.bmp'), sub, len(sub[0]), len(sub))
    print('  +', name, len(sub[0]), 'x', len(sub))
    return True

def autocut(px, w, h, prefix, scale=SCALE):
    """Нарезает связные области по сетке (для deaths-of-dave.png — 5 кадров 48x48)."""
    # deaths-of-dave.png имеет 5 кадров смерти в сетке
    # Пробуем разбить на фиксированные ячейки
    cell_w, cell_h = 48, 48
    n = 0
    for row in range(h // cell_h):
        for col in range(w // cell_w):
            x0, y0 = col * cell_w, row * cell_h
            # Проверяем, не пустая ли ячейка
            has_content = False
            for y in range(y0, min(y0+cell_h, h)):
                for x in range(x0, min(x0+cell_w, w)):
                    if not (px[y][x][3] < 128 or (px[y][x][0]+px[y][x][1]+px[y][x][2]) == 0):
                        has_content = True
                        break
                if has_content: break
            if has_content:
                cut_from(px, '%s%02d' % (prefix, n), x0, y0, cell_w, cell_h, w, h, scale)
                n += 1
    return n

FONT = {
'0':['111','101','101','101','111'], '1':['010','110','010','010','111'],
'2':['111','001','111','100','111'], '3':['111','001','011','001','111'],
'4':['101','101','111','001','001'], '5':['111','100','111','001','111'],
'6':['111','100','111','101','111'], '7':['111','001','001','001','001'],
'8':['111','101','111','101','111'], '9':['111','101','111','001','111'],
'_':['000','000','000','000','111'], 'a':['000','111','101','101','111'],
'b':['100','110','101','101','110'], 'd':['001','011','101','101','011'],
'e':['111','100','111','100','111'], 'g':['000','111','101','111','001'],
'i':['111','010','010','010','111'], 'j':['001','001','001','101','010'],
'l':['110','010','010','010','111'], 'o':['000','111','101','101','111'],
'p':['000','110','101','110','100'], 'r':['000','011','100','100','100'],
's':['000','111','100','111','001'], 't':['111','010','010','010','010'],
'w':['101','101','101','111','101'],
}
def set_px(px, x, y, c, W, H):
    if 0 <= x < W and 0 <= y < H: px[y][x] = c
def draw_rect(px, x, y, w, h, col, W, H):
    c = col + (255,)
    for i in range(x, x+w):
        set_px(px, i, y, c, W, H); set_px(px, i, y+h-1, c, W, H)
    for j in range(y, y+h):
        set_px(px, x, j, c, W, H); set_px(px, x+w-1, j, c, W, H)
def draw_text(px, x, y, s, col, W, H, sc=2):
    c = col + (255,); cx = x
    for ch in s:
        g = FONT.get(ch)
        if g:
            for r in range(5):
                for q in range(3):
                    if g[r][q] == '1':
                        for dy in range(sc):
                            for dx in range(sc):
                                set_px(px, cx+q*sc+dx, y+r*sc+dy, c, W, H)
        cx += 4*sc

# ---------- 1) атлас дэйва/врагов ----------
path = os.path.join(SHEET_DIR, 'dave.png')
if not os.path.exists(path):
    print('качаю атлас дэйва…'); urllib.request.urlretrieve(URL, path)
W, H, px = read_png(path)
print('атлас dave.png:', W, 'x', H)
for mod in anims.ALL:
    for name, x0, y0, fw, fh in mod.ATLAS:
        cut_from(px, name, x0, y0, fw, fh, W, H)
for i in range(9):
    cut_from(px, 'ammo_%d' % i, 1456 + 70 * i, 0, 70, 32, W, H)
for i, x in enumerate((2086, 2122, 2158, 2194)):
    cut_from(px, 'dave_door%d' % (i + 1), x, 0, 36, 64, W, H)

# ---------- 2) level01: ВСЕ объекты для аннотации, видимая статика (0/1/6) для нарезки ----------
try:
    lv_png = os.path.join(SHEET_DIR, 'level01.png')
    lv_txt = os.path.join(SHEET_DIR, 'levels.txt')
    if not os.path.exists(lv_png):
        print('качаю level01.png…'); urllib.request.urlretrieve(ROOT_URL + 'sprites/level01.png', lv_png)
    if not os.path.exists(lv_txt):
        print('качаю levels.txt…'); urllib.request.urlretrieve(ROOT_URL + 'levels.txt', lv_txt)
    LW, LH, lpx = read_png(lv_png)
    print('level01.png:', LW, 'x', LH)

    raw = json.load(open(lv_txt))
    if isinstance(raw, list):
        lvl_data = next((it for it in raw if isinstance(it, dict) and it.get('objects')), {})
    else:
        lvl_data = raw
    objs = lvl_data.get('objects', []) if isinstance(lvl_data, dict) else []
    print('объектов в уровне:', len(objs))

    entries = []
    step_seen = wall_seen = door_seen = False
    obj_n = 0
    
    for o in objs:
        if not isinstance(o, dict): continue
        t = o.get('type')
        x, y = int(o.get('x', 0)), int(o.get('y', 0))
        w, h = int(o.get('width', 0)), int(o.get('height', 0))
        if w <= 0 or h <= 0: continue
        
        # Определяем имя
        if t == 0:  # стена/блок
            if not wall_seen:
                cut_from(lpx, 'tile_wall', x + 32, y + 32, 32, 32, LW, LH)
                cut_from(lpx, 'tile_wall_top', x + 32, y, 32, 32, LW, LH)
                wall_seen = True
            name = 'wall_%03d' % obj_n
        elif t == 1:  # платформа/ступень
            if w == 84 and h == 32 and not step_seen:
                cut_from(lpx, 'stair_orig', x, y, w, h, LW, LH)
                cut_from(lpx, 'tile_plat', x, y, w, h, LW, LH)
                step_seen = True
            name = 'plat_%03d' % obj_n
        elif t == 2:  # зомби (спавн)
            name = 'zombie_spawn_%03d' % obj_n
        elif t == 3:  # гоблин (спавн)
            name = 'goblin_spawn_%03d' % obj_n
        elif t == 4:  # очки (бриллиант)
            name = 'gem_%03d' % obj_n
        elif t == 5:  # телепорт
            name = 'teleport_%03d' % obj_n
        elif t == 6:  # шкаф-дверь
            if not door_seen:
                cut_from(lpx, 'door_orig', x, y, w, h, LW, LH)
                door_seen = True
            name = 'door_%03d' % obj_n
        else:
            name = 'obj_%03d' % obj_n
        
        entries.append((name, x, y, w, h))
        obj_n += 1

    # карта с рамками и подписями
    ann = [row[:] for row in lpx]
    for name, x, y, w, h in entries:
        draw_rect(ann, x, y, w, h, (255, 0, 0), LW, LH)
        ty = y - 12 if y >= 12 else y + 2
        draw_text(ann, x + 2, ty, name, (255, 255, 0), LW, LH)
    write_png(os.path.join(SHEET_DIR, 'level01_annotated.png'), ann, LW, LH)
    print('карта с рамками: assets/sheets/level01_annotated.png')
    print('всего объектов:', obj_n)
except Exception as ex:
    print('  ! элементы уровня:', ex)

# ---------- 3) сцены гибели ----------
try:
    deaths_png = os.path.join(SHEET_DIR, 'deaths-of-dave.png')
    if not os.path.exists(deaths_png):
        print('качаю deaths-of-dave.png…')
        urllib.request.urlretrieve(RE_URL + 'deaths-of-dave.png', deaths_png)
    DW, DH, dpx = read_png(deaths_png)
    print('deaths-of-dave.png:', DW, 'x', DH)
    n = autocut(dpx, DW, DH, 'death_', scale=SCALE)
    print('сцен гибели нарезано:', n)
except Exception as ex:
    print('  ! сцены гибели:', ex)

print('Готово. Запускай: python main.py')
