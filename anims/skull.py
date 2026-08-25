# anims/skull.py — летучий череп: быстрый полёт
import math
NAME = 'skull'; FALLBACK = 'bat1'; DEFAULT = 'fly'
HITBOX = (13, 9)
ATLAS = []
ANIMS = {'fly': ((['bat1', 'bat2'],), 8)}

def anim_state(e): return 'fly'

def update(e, ctx):
    e['x'] = e['sx'] + math.sin(e['t'] * .03) * 85
    e['y'] = e['sy'] + math.sin(e['t'] * .09) * 13
    e['face'] = 1 if math.cos(e['t'] * .03) > 0 else -1
