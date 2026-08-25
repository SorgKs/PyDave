# strings.py — все текстовые константы (легко перевести на другой язык)

# HUD
HUD_LIVES_FMT   = 'x %d'
HUD_GEMS_FMT    = 'Кубки %d/%d'
HUD_SCORE_FMT   = 'СЧЁТ %d'
HUD_KEY_LABEL   = 'КЛЮЧ'
HUD_CONTROLS    = '[M] звук  [P] пауза  [R] заново'

# Всплывающие сообщения
MSG_NEED_KEY    = 'НУЖЕН КЛЮЧ!'
MSG_GOT_KEY     = 'КЛЮЧ ПОЛУЧЕН!'
MSG_EXTRA_LIFE  = '+ЖИЗНЬ'
MSG_GEM_SCORE   = '+100'
MSG_FULL_HP_BONUS = '+200'
MSG_ENEMY_SCORE_FMT = '+%d'

# Очки за врагов (ключ — тип врага)
ENEMY_SCORE = {
    'z': 150,   # зомби
    'g': 200,   # призрак
    'b': 100,   # летучая мышь
}
GEM_SCORE = 100
KEY_SCORE = 300
FULL_HP_BONUS = 200

# Экраны
TITLE_BIG       = 'DAVE DANGEROUS'
TITLE_SUB       = 'ОСОБНЯК С ПРИВИДЕНИЯМИ'
TITLE_HINT_1    = 'Стрелки / AD — движение, ПРОБЕЛ — прыжок'
TITLE_HINT_2    = 'X / J — выстрел, ВНИЗ — спрыгнуть с помоста'
TITLE_HINT_3    = 'Собери кубки, найди ключ и выберись из особняка!'
TITLE_PROMPT    = 'НАЖМИ ENTER'

PAUSE_TITLE     = 'ПАУЗА'

GAMEOVER_TITLE  = 'ИГРА ОКОНЧЕНА'
GAMEOVER_SCORE  = 'СЧЁТ: %d'
GAMEOVER_PROMPT = 'ENTER — заново'

WIN_TITLE       = 'УРОВЕНЬ ПРОЙДЕН!'
WIN_SUBTITLE    = 'Дэйв сбежал из особняка...'
WIN_SCORE       = 'СЧЁТ: %d'
WIN_PROMPT      = 'ENTER — ещё раз'

# Окно
WINDOW_TITLE    = 'DAVE DANGEROUS — Haunted Mansion'
ERROR_NO_PYGAME = 'нужен pygame:  pip install pygame'
ERROR_NO_ASSETS = 'Папка assets не найдена. Сначала выполните:  python gen_assets.py'
