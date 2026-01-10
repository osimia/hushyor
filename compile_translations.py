#!/usr/bin/env python
"""
Скрипт для компиляции .po файлов в .mo без использования gettext
Использует встроенную библиотеку Python
"""
import os
import sys
from pathlib import Path

# Добавляем корневую директорию проекта в путь
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

def compile_po_to_mo(po_file_path):
    """
    Компилирует .po файл в .mo используя Python
    """
    try:
        import polib
    except ImportError:
        print("Установка polib...")
        os.system(f"{sys.executable} -m pip install polib")
        import polib
    
    mo_file_path = po_file_path.replace('.po', '.mo')
    
    try:
        po = polib.pofile(po_file_path)
        po.save_as_mofile(mo_file_path)
        print(f"✅ Скомпилировано: {po_file_path} -> {mo_file_path}")
        return True
    except Exception as e:
        print(f"❌ Ошибка при компиляции {po_file_path}: {e}")
        return False

def main():
    """
    Находит все .po файлы и компилирует их в .mo
    """
    locale_dir = BASE_DIR / 'locale'
    
    if not locale_dir.exists():
        print(f"❌ Директория {locale_dir} не найдена")
        return
    
    print("🔄 Начинаем компиляцию переводов...\n")
    
    po_files = list(locale_dir.rglob('*.po'))
    
    if not po_files:
        print("❌ Не найдено .po файлов для компиляции")
        return
    
    success_count = 0
    for po_file in po_files:
        if compile_po_to_mo(str(po_file)):
            success_count += 1
    
    print(f"\n✨ Готово! Скомпилировано {success_count} из {len(po_files)} файлов")
    
    if success_count == len(po_files):
        print("\n🎉 Все переводы успешно скомпилированы!")
        print("Теперь запустите сервер: python manage.py runserver")
    else:
        print("\n⚠️ Некоторые файлы не были скомпилированы. Проверьте ошибки выше.")

if __name__ == '__main__':
    main()
