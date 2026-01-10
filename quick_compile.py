#!/usr/bin/env python
"""Быстрая компиляция переводов без зависимостей"""
import struct
from pathlib import Path

def generate_mo_file(po_file_path, mo_file_path):
    """Генерирует .mo файл из .po файла"""
    
    # Читаем .po файл
    with open(po_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Парсим переводы
    translations = {}
    lines = content.split('\n')
    msgid = None
    msgstr = None
    in_msgid = False
    in_msgstr = False
    
    for line in lines:
        line = line.strip()
        
        if line.startswith('msgid "'):
            msgid = line[7:-1]
            in_msgid = True
            in_msgstr = False
        elif line.startswith('msgstr "'):
            msgstr = line[8:-1]
            in_msgid = False
            in_msgstr = True
        elif line.startswith('"') and (in_msgid or in_msgstr):
            # Продолжение многострочного текста
            text = line[1:-1]
            if in_msgid:
                msgid += text
            elif in_msgstr:
                msgstr += text
        elif line == '' or line.startswith('#'):
            # Конец записи
            if msgid is not None and msgstr is not None and msgid != '':
                translations[msgid] = msgstr
            msgid = None
            msgstr = None
            in_msgid = False
            in_msgstr = False
    
    # Последняя запись
    if msgid is not None and msgstr is not None and msgid != '':
        translations[msgid] = msgstr
    
    # Добавляем пустую запись для метаданных
    METADATA = (
        'Content-Type: text/plain; charset=UTF-8\n'
        'Content-Transfer-Encoding: 8bit\n'
    )
    
    # Создаем .mo файл
    keys = [''] + sorted(translations.keys())
    values = [METADATA] + [translations[k] for k in keys[1:]]
    
    ids = [key.encode('utf-8') for key in keys]
    strs = [value.encode('utf-8') for value in values]
    
    # Заголовок .mo файла
    keystart = 7 * 4 + 16 * len(keys)
    valuestart = keystart + sum(len(k) + 1 for k in ids)
    
    # Создаем бинарный файл
    with open(mo_file_path, 'wb') as f:
        # Magic number (little-endian)
        f.write(struct.pack('<I', 0x950412de))
        # Version
        f.write(struct.pack('<I', 0))
        # Number of entries
        f.write(struct.pack('<I', len(keys)))
        # Offset of table with original strings
        f.write(struct.pack('<I', 7 * 4))
        # Offset of table with translation strings
        f.write(struct.pack('<I', 7 * 4 + len(keys) * 8))
        # Size of hashing table
        f.write(struct.pack('<I', 0))
        # Offset of hashing table
        f.write(struct.pack('<I', 0))
        
        # Write key offsets and lengths
        offset = keystart
        for key in ids:
            f.write(struct.pack('<I', len(key)))
            f.write(struct.pack('<I', offset))
            offset += len(key) + 1
        
        # Write value offsets and lengths
        offset = valuestart
        for value in strs:
            f.write(struct.pack('<I', len(value)))
            f.write(struct.pack('<I', offset))
            offset += len(value) + 1
        
        # Write keys
        for key in ids:
            f.write(key)
            f.write(b'\x00')
        
        # Write values
        for value in strs:
            f.write(value)
            f.write(b'\x00')
    
    print(f"✅ Создан: {mo_file_path}")

# Компилируем оба языка
base_dir = Path(__file__).parent
locale_dir = base_dir / 'locale'

# Таджикский
tg_po = locale_dir / 'tg' / 'LC_MESSAGES' / 'django.po'
tg_mo = locale_dir / 'tg' / 'LC_MESSAGES' / 'django.mo'

# Русский
ru_po = locale_dir / 'ru' / 'LC_MESSAGES' / 'django.po'
ru_mo = locale_dir / 'ru' / 'LC_MESSAGES' / 'django.mo'

print("🔄 Компиляция переводов...\n")

if tg_po.exists():
    generate_mo_file(str(tg_po), str(tg_mo))
else:
    print(f"❌ Не найден: {tg_po}")

if ru_po.exists():
    generate_mo_file(str(ru_po), str(ru_mo))
else:
    print(f"❌ Не найден: {ru_po}")

print("\n🎉 Готово! Переводы скомпилированы.")
print("Перезапустите сервер: python manage.py runserver")
