# anims/ghost.py — призрак: синусоидальный полёт
import math
NAME = 'ghost'; FALLBACK = 'ghost1'; DEFAULT = 'fly'
HITBOX = (12, 13)
ATLAS = []
ANIMS = {'fly': ((['ghost1', 'ghost2'],), 3)}

def anim_state(e): return 'fly'

def update(e, ctx):
    e['x'] = e['sx'] + math.sin(e['t'] * .013) * 70
    e['y'] = e['sy'] + math.sin(e['t'] * .05) * 9
    e['face'] = 1 if math.cos(e['t'] * .013) > 0 else -1
