#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
import pygame
pygame.init()
pygame.display.set_mode((1, 1))
from assets import load_all_sprites

I = load_all_sprites()
print(f"Загружено спрайтов: {len(I)}")
print("\nСтатические (прямо из STATIC_SPRITES):")
for k in sorted(I.keys()):
    if k in ['spike', 'heart', 'door_closed', 'door_open', 'ammo_0', 'ammo_1', 'ammo_2', 'ammo_3', 'ammo_4', 'ammo_5', 'ammo_6', 'ammo_7', 'ammo_8', 'dave_reload1', 'dave_reload2', 'dave_death_zombie1', 'dave_death_zombie2', 'dave_death_zombie3', 'dave_death_zombie4', 'dave_death_zombie5']:
        print(f"  {k}")
print("\nИз anims (object sprites):")
# collect anims sprites via collect_sprites_maps
from anims import collect_sprites_maps
anims_sprites = collect_sprites_maps()
for k in sorted(anims_sprites.keys()):
    print(f"  {k}")
    
# Show keys that are only in I but not in anims_sprites
print("\nТолько в I (возможно статические):")
only_i = set(I.keys()) - set(anims_sprites.keys())
for k in sorted(only_i):
    print(f"  {k}")