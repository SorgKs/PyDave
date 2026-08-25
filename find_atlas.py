#!/usr/bin/env python3
# find_atlas_in_js.py — ищем координаты атласа в JS-файлах репозитория
import requests
import re

REPO_OWNER = "lightest"
REPO_NAME = "webdave"
BRANCH = "master"

# Наиболее вероятные файлы с координатами атласа
JS_FILES_TO_CHECK = [
    "player.js",
    "character.js", 
    "Sprite.js",
    "Game.js",
    "app.js"
]

def download_js_file(filepath):
    """Скачивает содержимое JS-файла"""
    url = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{BRANCH}/{filepath}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    return None

def search_for_atlas_patterns(content, filename):
    """Ищет паттерны определения атласа в JS-коде"""
    print(f"\n🔍 Анализируем {filename}...")
    
    # Паттерны для поиска координат
    patterns = [
        # Массивы с x, y, width, height
        r'\{[^}]*x:\s*\d+[^}]*y:\s*\d+[^}]*width:\s*\d+[^}]*height:\s*\d+[^}]*\}',
        r'\{[^}]*x:\s*\d+[^}]*y:\s*\d+[^}]*w:\s*\d+[^}]*h:\s*\d+[^}]*\}',
        
        # Массивы кадров
        r'ATLAS\s*=\s*\[[\s\S]*?\]',
        r'frames\s*=\s*\[[\s\S]*?\]',
        r'sprites\s*=\s*\[[\s\S]*?\]',
        
        # Определения с именами
        r'["\']\w+["\']:\s*\{[^}]*x:\s*\d+[^}]*y:\s*\d+[^}]*\}',
    ]
    
    found_something = False
    for pattern in patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            found_something = True
            print(f"  ✅ Найдено {len(matches)} совпадений с паттерном")
            # Показываем первые 3 совпадения
            for i, match in enumerate(matches[:3]):
                preview = match[:200].replace('\n', ' ')
                print(f"     [{i+1}] {preview}...")
            if len(matches) > 3:
                print(f"     ... и ещё {len(matches) - 3}")
    
    if not found_something:
        print(f"  ❌ Координаты не найдены")
    
    return found_something

def main():
    print(f"🔍 Ищем координаты атласа в JS-файлах репозитория...\n")
    
    for filepath in JS_FILES_TO_CHECK:
        content = download_js_file(filepath)
        if content:
            print(f"📄 Скачан {filepath} ({len(content)} байт)")
            search_for_atlas_patterns(content, filepath)
        else:
            print(f"❌ Не удалось скачать {filepath}")

if __name__ == "__main__":
    main()