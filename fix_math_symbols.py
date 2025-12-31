import json
import re
from pathlib import Path

def fix_math_symbols(text):
    """Исправляет все сломанные математические символы"""
    
    # Словарь замен для Oriya цифр на надстрочные символы
    oriya_to_superscript = {
        '୦': '⁰',
        '୧': '¹',
        '୨': '²',
        '୩': '³',
        '୪': '⁴',
        '୫': '⁵',
        '୬': '⁶',
        '୭': '⁷',
        '୮': '⁸',
        '୯': '⁹',
        'ି': '⁻',  # Oriya знак минус
        'ା': '⁺',  # Oriya знак плюс
    }
    
    # 1. Заменяем математический italic x на обычный x
    text = text.replace('𝑥', 'x')
    
    # 2. Заменяем Sinhala корень на правильный корень
    text = text.replace('ඥ', '√')
    
    # 3. Заменяем другие математические italic буквы
    text = text.replace('𝑦', 'y')
    text = text.replace('𝑙', 'l')
    text = text.replace('𝑜', 'o')
    text = text.replace('𝑔', 'g')
    text = text.replace('𝑡', 't')
    
    # 4. Заменяем Oriya цифры на надстрочные
    for oriya, superscript in oriya_to_superscript.items():
        text = text.replace(oriya, superscript)
    
    # 5. Исправляем специфические паттерны
    # x⁻² вместо x ⁻2 (убираем пробелы перед степенями)
    text = re.sub(r'([a-zA-Z])\s+([⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻]+)', r'\1\2', text)
    
    # 6. Исправляем паттерны типа "x ⁻ 2" -> "x⁻²"
    text = re.sub(r'x\s*⁻\s*(\d+)', lambda m: f'x⁻{to_superscript(m.group(1))}', text)
    
    return text

def to_superscript(num_str):
    """Конвертирует обычные цифры в надстрочные"""
    superscript_map = {
        '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴',
        '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹'
    }
    return ''.join(superscript_map.get(c, c) for c in num_str)

def contains_broken_symbols(text):
    """Проверяет наличие сломанных символов"""
    broken_patterns = [
        r'[ି-୯]',      # Oriya digits
        r'[ඉ-෯]',      # Sinhala letters
        r'𝑥',          # Mathematical italic x
        r'𝑦',          # Mathematical italic y
    ]
    
    for pattern in broken_patterns:
        if re.search(pattern, text):
            return True
    return False

def fix_json_data(data):
    """Исправляет математические символы во всех заданиях"""
    
    fixed_count = 0
    changes = []
    
    for item in data:
        if item['model'] != 'core.task':
            continue
        
        fields = item['fields']
        task_id = item['pk']
        task_changed = False
        
        # Проверяем и исправляем вопрос
        if 'question' in fields:
            original = fields['question']
            if contains_broken_symbols(original):
                fixed = fix_math_symbols(original)
                if fixed != original:
                    changes.append({
                        'task_id': task_id,
                        'field': 'question',
                        'original': original,
                        'fixed': fixed
                    })
                    fields['question'] = fixed
                    task_changed = True
        
        # Проверяем и исправляем варианты ответов
        if 'options' in fields:
            for key, value in fields['options'].items():
                if contains_broken_symbols(value):
                    fixed = fix_math_symbols(value)
                    if fixed != value:
                        changes.append({
                            'task_id': task_id,
                            'field': f'option_{key}',
                            'original': value,
                            'fixed': fixed
                        })
                        fields['options'][key] = fixed
                        task_changed = True
        
        if task_changed:
            fixed_count += 1
    
    return data, changes, fixed_count

def main():
    print("=" * 80)
    print("🔧 ИСПРАВЛЕНИЕ МАТЕМАТИЧЕСКИХ СИМВОЛОВ В JSON")
    print("=" * 80)
    
    json_file = Path(__file__).parent / 'hushyor_data.json'
    
    if not json_file.exists():
        print(f"❌ Файл не найден: {json_file}")
        return
    
    print(f"\n📂 Загрузка файла: {json_file.name}")
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"✅ Загружено {len(data)} записей")
    
    # Исправляем данные
    print("\n🔍 Поиск и исправление сломанных символов...")
    
    fixed_data, changes, fixed_count = fix_json_data(data)
    
    if not changes:
        print("\n✅ Сломанных символов не найдено! Все в порядке.")
        return
    
    # Показываем первые 10 изменений
    print(f"\n📊 Найдено заданий с проблемами: {fixed_count}")
    print(f"📝 Всего изменений: {len(changes)}")
    print("\n🔍 Примеры исправлений (первые 10):")
    print("-" * 80)
    
    for i, change in enumerate(changes[:10], 1):
        print(f"\n{i}. Задание #{change['task_id']} - {change['field']}:")
        print(f"   ❌ Было: {change['original']}")
        print(f"   ✅ Стало: {change['fixed']}")
    
    if len(changes) > 10:
        print(f"\n... и еще {len(changes) - 10} изменений")
    
    # Спрашиваем подтверждение
    print("\n" + "=" * 80)
    response = input("\n❓ Применить все исправления? (yes/no): ").strip().lower()
    
    if response not in ['yes', 'y', 'да', 'д']:
        print("❌ Отменено пользователем")
        return
    
    # Создаем резервную копию
    backup_file = json_file.with_suffix('.json.backup')
    print(f"\n💾 Создание резервной копии: {backup_file.name}")
    
    with open(json_file, 'r', encoding='utf-8') as f:
        original_data = f.read()
    
    with open(backup_file, 'w', encoding='utf-8') as f:
        f.write(original_data)
    
    # Сохраняем исправленный файл
    print(f"💾 Сохранение исправлений: {json_file.name}")
    
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(fixed_data, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 80)
    print(f"✅ ГОТОВО!")
    print(f"📊 Исправлено заданий: {fixed_count}")
    print(f"📝 Всего изменений: {len(changes)}")
    print(f"📁 Резервная копия: {backup_file.name}")
    print("=" * 80)
    
    # Сохраняем отчет об изменениях
    report_file = Path(__file__).parent / 'fix_report.txt'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("ОТЧЕТ ОБ ИСПРАВЛЕНИИ МАТЕМАТИЧЕСКИХ СИМВОЛОВ\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Всего изменений: {len(changes)}\n")
        f.write(f"Исправлено заданий: {fixed_count}\n\n")
        f.write("ДЕТАЛИ ИЗМЕНЕНИЙ:\n")
        f.write("-" * 80 + "\n\n")
        
        for i, change in enumerate(changes, 1):
            f.write(f"{i}. Задание #{change['task_id']} - {change['field']}:\n")
            f.write(f"   Было: {change['original']}\n")
            f.write(f"   Стало: {change['fixed']}\n\n")
    
    print(f"📄 Детальный отчет сохранен: {report_file.name}")

if __name__ == '__main__':
    main()
