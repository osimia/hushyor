#!/usr/bin/env python3
"""
Скрипт для добавления правильных ответов к тестам по истории
"""

import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

# Загружаем переменные из .env файла
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Настройка Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    print("❌ Ошибка: GEMINI_API_KEY не найден в .env файле")
    print("Добавьте в .env файл: GEMINI_API_KEY=your-api-key-here")
    sys.exit(1)

genai.configure(api_key=GEMINI_API_KEY)

def extract_answers_from_pdf(pdf_path):
    """
    Извлекает правильные ответы из PDF файла с ключами
    """
    
    print(f"Загрузка PDF файла с ответами: {pdf_path}")
    
    pdf_file = genai.upload_file(pdf_path)
    print(f"✅ Файл загружен: {pdf_file.display_name}")
    
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = """
Извлеки все правильные ответы из этого PDF файла.

ВАЖНО: Верни результат ТОЛЬКО в формате JSON.

Формат JSON:
{
  "answers": {
    "1": "A",
    "2": "B",
    "3": "C",
    ...
  }
}

Правила:
1. Ключи - номера тестов (строки)
2. Значения - правильные ответы (A, B, C или D - латинские буквы)
3. Если в PDF ответы обозначены как А, В, С, D (кириллица) - конвертируй в A, B, C, D (латиница)
4. Верни ТОЛЬКО валидный JSON

Верни ТОЛЬКО валидный JSON, без ```json``` и текста.
"""
    
    print("Отправка запроса к Gemini API...")
    response = model.generate_content([pdf_file, prompt])
    
    print("✅ Получен ответ от Gemini")
    
    try:
        response_text = response.text.strip()
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.startswith('```'):
            response_text = response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        data = json.loads(response_text)
        answers = data.get('answers', {})
        
        # Конвертируем ключи в int
        answers_dict = {int(k): v for k, v in answers.items()}
        
        print(f"✅ Извлечено {len(answers_dict)} ответов")
        
        return answers_dict
        
    except (json.JSONDecodeError, ValueError) as e:
        print(f"❌ Ошибка парсинга JSON: {e}")
        print(f"\nОтвет Gemini (первые 500 символов):")
        print(response.text[:500])
        
        # Сохраняем для анализа
        with open('gemini_answers_debug.txt', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print(f"Полный ответ сохранен в gemini_answers_debug.txt")
        
        return {}

def add_answers_to_json(json_file, answers):
    """
    Добавляет правильные ответы к существующему JSON файлу с тестами
    """
    
    print(f"\nЧтение файла: {json_file}")
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Добавляем ответы к тестам
    total_updated = 0
    total_missing = 0
    
    for topic in data['topics']:
        for task in topic['tasks']:
            test_num = task['original_test_id']
            if test_num in answers:
                task['correct_answer'] = answers[test_num]
                total_updated += 1
            else:
                total_missing += 1
                print(f"⚠️  Ответ не найден для теста #{test_num}")
    
    # Сохраняем обновленный файл
    output_file = json_file.replace('.json', '_with_answers.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*60}")
    print(f"✅ Обновленные данные сохранены в {output_file}")
    print(f"{'='*60}")
    print(f"Обновлено тестов: {total_updated}")
    print(f"Без ответов: {total_missing}")
    
    return output_file

def main():
    # Файлы
    answers_pdf = "A2-34_History_tj_key.pdf"  # Файл с ключами
    tests_json = "history_tests_import.json"   # JSON с тестами
    
    # Проверяем наличие файлов
    if not os.path.exists(answers_pdf):
        print(f"❌ Файл с ответами не найден: {answers_pdf}")
        print("\nПоместите файл с ключами в текущую директорию")
        return
    
    if not os.path.exists(tests_json):
        print(f"❌ Файл с тестами не найден: {tests_json}")
        print("\nСначала запустите: python extract_history_tests.py")
        return
    
    # Извлекаем ответы из PDF
    answers = extract_answers_from_pdf(answers_pdf)
    
    if not answers:
        print("❌ Не удалось извлечь ответы")
        return
    
    # Добавляем ответы к тестам
    output_file = add_answers_to_json(tests_json, answers)
    
    print(f"\n✅ Готово! Теперь можете импортировать: {output_file}")

if __name__ == '__main__':
    main()
