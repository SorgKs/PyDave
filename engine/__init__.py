# engine/__init__.py — новый игровой движок (рефакторинг)
"""
Архитектура:
- physics: универсальная физика + коллизии (2 прохода)
- anims/obj: логика объектов (init, behave, transform, get_sprite)
- render: отрисовка тайлов и объектов
- level: источник истины (генерирует tilemap и surface_map)
"""

__all__ = ['physics', 'objects', 'render']
