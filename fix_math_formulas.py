import json
import os
import re
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-2.0-flash-exp')

def contains_broken_math(text):
    """Проверяет, содержит ли текст сломанные математические символы"""
    broken_patterns = [
        r'[ି-୯]',  # Oriya digits (неправильные символы)
        r'𝑥[ି-୯]',  # Математический x с неправильными степенями
        r'[a-zA-Z][ି-୯]',  # Латинские буквы с неправильными символами
    ]
    
    for pattern in broken_patterns:
        if re.search(pattern, text):
            return True
    return False

def fix_math_with_ai(text, context=""):
    """Исправляет математические формулы с помощью AI"""
    
    prompt = f"""Ты математический эксперт. Исправь математические формулы в следующем тексте.

ПРОБЛЕМА: В тексте используются неправильные Unicode символы (Oriya digits) вместо нормальных математических обозначений.

ПРАВИЛА ИСПРАВЛЕНИЯ:
1. Символы ି, ୧, ୨, ୩, ୪, ୫, ୬, ୭, ୮, ୯ - это НЕПРАВИЛЬНЫЕ символы (Oriya digits)
2. Замени их на правильные математические обозначения:
   - xି2 → x^(-2) или x⁻²
   - xିଷ → x^(-3) или x⁻³
   - xିଵ → x^(-1) или x⁻¹
   - x² → x² (оставь как есть, это правильно)
   - x³ → x³ (оставь как есть, это правильно)

3. Используй Unicode надстрочные символы для степеней: ⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻
4. Для отрицательных степеней используй: x⁻¹, x⁻², x⁻³ и т.д.
5. Сохрани все остальные части текста БЕЗ ИЗМЕНЕНИЙ

КОНТЕКСТ: {context}

ТЕКСТ ДЛЯ ИСПРАВЛЕНИЯ:
{text}

ВАЖНО: Верни ТОЛЬКО исправленный текст, без объяснений и дополнительных слов."""

    try:
        response = model.generate_content(prompt)
        fixed_text = response.text.strip()
        
        # Убираем возможные markdown форматирование
        fixed_text = fixed_text.replace('```', '').strip()
        
        return fixed_text
    except Exception as e:
        print(f"⚠ Ошибка AI: {e}")
        return text

def fix_task_item(task, dry_run=True):
    """Исправляет математические формулы в одном задании"""
    
    if task['model'] != 'core.task':
        return task, False
    
    changed = False
    fields = task['fields']
    
    # Проверяем вопрос
    if 'question' in fields and contains_broken_math(fields['question']):
        original = fields['question']
        context = f"Это вопрос математического задания #{task['pk']}"
        fixed = fix_math_with_ai(original, context)
        
        if fixed != original:
            print(f"\n📝 Задание #{task['pk']} - ВОПРОС:")
            print(f"  ❌ Было: {original}")
            print(f"  ✅ Стало: {fixed}")
            
            if not dry_run:
                fields['question'] = fixed
            changed = True
    
    # Проверяем варианты ответов
    if 'options' in fields:
        for key, value in fields['options'].items():
            if contains_broken_math(value):
                original = value
                context = f"Это вариант ответа #{key} для задания #{task['pk']}"
                fixed = fix_math_with_ai(original, context)
                
                if fixed != original:
                    print(f"\n📝 Задание #{task['pk']} - Вариант {key}:")
                    print(f"  ❌ Было: {original}")
                    print(f"  ✅ Стало: {fixed}")
                    
                    if not dry_run:
                        fields['options'][key] = fixed
                    changed = True
    
    return task, changed

def main():
    print("=" * 80)
    print("🔧 ИСПРАВЛЕНИЕ МАТЕМАТИЧЕСКИХ ФОРМУЛ В JSON")
    print("=" * 80)
    
    json_file = Path(__file__).parent / 'hushyor_data.json'
    
    if not json_file.exists():
        print(f"❌ Файл не найден: {json_file}")
        return
    
    # Проверяем API ключ
    if not os.getenv('GEMINI_API_KEY'):
        print("❌ GEMINI_API_KEY не найден в .env файле!")
        return
    
    print(f"\n📂 Загрузка файла: {json_file}")
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"✅ Загружено {len(data)} записей")
    
    # Первый проход - проверка (dry run)
    print("\n" + "=" * 80)
    print("🔍 ШАГ 1: ПРОВЕРКА (без изменений)")
    print("=" * 80)
    
    tasks_to_fix = []
    for item in data:
        if item['model'] == 'core.task':
            _, has_issues = fix_task_item(item, dry_run=True)
            if has_issues:
                tasks_to_fix.append(item['pk'])
    
    print(f"\n📊 Найдено заданий с проблемами: {len(tasks_to_fix)}")
    
    if not tasks_to_fix:
        print("✅ Все формулы в порядке!")
        return
    
    # Спрашиваем подтверждение
    print("\n" + "=" * 80)
    response = input("\n❓ Применить исправления? (yes/no): ").strip().lower()
    
    if response not in ['yes', 'y', 'да', 'д']:
        print("❌ Отменено пользователем")
        return
    
    # Второй проход - применение изменений
    print("\n" + "=" * 80)
    print("✏️ ШАГ 2: ПРИМЕНЕНИЕ ИСПРАВЛЕНИЙ")
    print("=" * 80)
    
    fixed_count = 0
    for item in data:
        if item['model'] == 'core.task' and item['pk'] in tasks_to_fix:
            _, changed = fix_task_item(item, dry_run=False)
            if changed:
                fixed_count += 1
    
    # Создаем резервную копию
    backup_file = json_file.with_suffix('.json.backup')
    print(f"\n💾 Создание резервной копии: {backup_file}")
    
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # Сохраняем исправленный файл
    print(f"💾 Сохранение исправлений: {json_file}")
    
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 80)
    print(f"✅ ГОТОВО! Исправлено заданий: {fixed_count}")
    print(f"📁 Резервная копия: {backup_file}")
    print("=" * 80)

if __name__ == '__main__':
    main()
