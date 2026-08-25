#!/usr/bin/env python3
# debug_repo.py — диагностика содержимого репозитория
import requests

REPO_OWNER = "lightest"
REPO_NAME = "webdave"

def list_repo_files():
    print(f"🔍 Сканируем репозиторий {REPO_OWNER}/{REPO_NAME}...\n")
    
    for branch in ['main', 'master']:
        url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/git/trees/{branch}?recursive=1"
        print(f"Проверяем ветку: {branch}")
        
        try:
            response = requests.get(url, timeout=10)
            print(f"Статус ответа: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                tree = data.get('tree', [])
                
                print(f"\n📁 Найдено {len(tree)} объектов:\n")
                
                # Группируем по типам
                files_by_ext = {}
                for item in tree:
                    if item['type'] == 'blob':
                        path = item['path']
                        ext = path.split('.')[-1] if '.' in path else 'no_ext'
                        if ext not in files_by_ext:
                            files_by_ext[ext] = []
                        files_by_ext[ext].append(path)
                
                # Выводим статистику
                print("📊 Статистика по типам файлов:")
                for ext, files in sorted(files_by_ext.items()):
                    print(f"  .{ext}: {len(files)} файлов")
                
                # Выводим все JSON файлы
                print(f"\n📄 JSON файлы:")
                json_files = files_by_ext.get('json', [])
                if json_files:
                    for f in json_files:
                        print(f"  - {f}")
                else:
                    print("  ❌ JSON файлы не найдены")
                
                # Выводим все файлы с изображениями
                print(f"\n🖼️  Файлы изображений:")
                img_files = files_by_ext.get('png', []) + files_by_ext.get('jpg', []) + files_by_ext.get('gif', [])
                if img_files:
                    for f in img_files[:20]:  # Показываем первые 20
                        print(f"  - {f}")
                    if len(img_files) > 20:
                        print(f"  ... и ещё {len(img_files) - 20}")
                else:
                    print("  ❌ Изображения не найдены")
                
                # Выводим все файлы
                print(f"\n📂 Все файлы (первые 50):")
                all_files = [item['path'] for item in tree if item['type'] == 'blob']
                for f in all_files[:50]:
                    print(f"  - {f}")
                if len(all_files) > 50:
                    print(f"  ... и ещё {len(all_files) - 50}")
                
                return
                
            elif response.status_code == 403:
                print("⚠️  Превышен лимит запросов GitHub API")
                print("   Попробуйте позже или используйте токен")
            elif response.status_code == 404:
                print(f"❌ Ветка {branch} не существует")
            else:
                print(f"❌ Ошибка: {response.text}")
                
        except Exception as e:
            print(f"❌ Исключение: {e}")
        
        print()

if __name__ == "__main__":
    list_repo_files()