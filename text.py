# text.py — работа с текстом и шрифтами
import pygame
from config import WW, WH

# Глобальные настройки
FONT_OK = False
_FC = {}

def init_font():
    """Инициализация системы шрифтов"""
    global FONT_OK
    try:
        import pygame.font
        pygame.font.init()
        pygame.font.Font(None, 20)
        FONT_OK = True
    except Exception:
        FONT_OK = False
    return FONT_OK

def font(sz):
    """Возвращает шрифт указанного размера"""
    if not FONT_OK:
        return None
    if sz not in _FC:
        _FC[sz] = pygame.font.Font(None, sz)
    return _FC[sz]

def C(c):
    """
    Преобразует цвет в формат, понятный Pygame.
    Поддерживает:
    - hex цвета: #fff, #ffd23f
    - именованные цвета: white, black, red и т.д.
    - RGB кортежи: (255, 255, 255)
    """
    if isinstance(c, str):
        if c.startswith('#'):
            h = c.lstrip('#')
            if len(h) == 3:
                h = h[0]*2 + h[1]*2 + h[2]*2
            return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
        # Если это имя цвета, возвращаем как есть (Pygame его поймет)
        return c
    return c

def text_out(surf, s, x, y, size, col, center=False):
    """
    Отрисовывает текст с тенью.
    
    Параметры:
    - surf: поверхность для отрисовки
    - s: текстовая строка
    - x, y: координаты
    - size: размер шрифта
    - col: цвет (hex, имя или RGB)
    - center: центрировать ли текст
    """
    f = font(size)
    if not f:
        return
    
    color = C(col)
    black = (0, 0, 0)
    
    im = f.render(s, True, color)
    sh = f.render(s, True, black)
    
    r = im.get_rect(center=(x, y)) if center else im.get_rect(topleft=(x, y))
    
    # Тень со смещением
    surf.blit(sh, (r.x + 2, r.y + 2))
    surf.blit(im, r)

def text_out_no_shadow(surf, s, x, y, size, col, center=False):
    """
    Отрисовывает текст без тени.
    """
    f = font(size)
    if not f:
        return
    
    color = C(col)
    im = f.render(s, True, color)
    r = im.get_rect(center=(x, y)) if center else im.get_rect(topleft=(x, y))
    surf.blit(im, r)

def text_size(s, size):
    """
    Возвращает размер текста (ширина, высота) в пикселях.
    """
    f = font(size)
    if not f:
        return (0, 0)
    return f.size(s)

def get_font_ok():
    """Возвращает статус доступности шрифтов"""
    return FONT_OK

def overlay(surf, col=(5, 3, 12, 150)):
    """
    Создает полупрозрачное наложение на всю поверхность.
    
    Параметры:
    - surf: поверхность для отрисовки
    - col: цвет в формате RGBA (R, G, B, Alpha)
    """
    s = pygame.Surface((WW, WH), pygame.SRCALPHA)
    s.fill(col)
    surf.blit(s, (0, 0))

def draw_centered_text(surf, s, y, size, col, shadow=True):
    """
    Выводит центрированный текст по горизонтали.
    """
    f = font(size)
    if not f:
        return
    
    color = C(col)
    black = (0, 0, 0)
    
    im = f.render(s, True, color)
    if shadow:
        sh = f.render(s, True, black)
        x = (WW - im.get_width()) // 2
        surf.blit(sh, (x + 2, y + 2))
        surf.blit(im, (x, y))
    else:
        x = (WW - im.get_width()) // 2
        surf.blit(im, (x, y))

def draw_centered_text_xy(surf, s, x, y, size, col, shadow=True):
    """
    Выводит текст с центром в указанной точке.
    """
    f = font(size)
    if not f:
        return
    
    color = C(col)
    black = (0, 0, 0)
    
    im = f.render(s, True, color)
    rect = im.get_rect(center=(x, y))
    
    if shadow:
        sh = f.render(s, True, black)
        sh_rect = sh.get_rect(center=(x + 2, y + 2))
        surf.blit(sh, sh_rect)
    
    surf.blit(im, rect)