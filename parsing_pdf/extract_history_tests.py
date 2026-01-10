#!/usr/bin/env python3
"""
Скрипт для извлечения тестов по истории из PDF с помощью Gemini API
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Загружаем переменные из .env файла
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Настройка Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    print("❌ Ошибка: GEMINI_API_KEY не найден в .env файле")
    print("Добавьте в .env файл: GEMINI_API_KEY=your-api-key-here")
    sys.exit(1)

MODEL_NAME = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash')

try:
    client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as exc:
    print(f"❌ Не удалось создать клиента Gemini: {exc}")
    sys.exit(1)

def extract_history_tests(pdf_path):
    """
    Извлекает тесты по истории из PDF файла
    """
    
    print(f"Загрузка PDF файла: {pdf_path}")
    
    # Загружаем PDF файл
    try:
        pdf_file = client.files.upload(file=pdf_path)
    except Exception as exc:
        print(f"❌ Ошибка загрузки файла: {exc}")
        return []

    print(f"✅ Файл загружен: {pdf_file.display_name}")
    
    # Промпт для извлечения тестов
    prompt = """
Извлеки все тесты из этого PDF файла по предмету "Таърих" (История).

КРИТИЧЕСКИ ВАЖНО:
- Текст на ТАДЖИКСКОМ языке (кириллица с буквами ғ, қ, ҳ, ҷ, ӣ, ӯ)
- Сохраняй ВСЕ таджикские буквы ТОЧНО как в оригинале
- Верни результат ТОЛЬКО в формате JSON

Формат JSON:
{
  "tests": [
    {
      "number": 1,
      "question": "Текст вопроса на таджикском",
      "options": {
        "A": "Вариант A",
        "B": "Вариант B",
        "C": "Вариант C",
        "D": "Вариант D"
      }
    }
  ]
}

Правила:
1. ОБЯЗАТЕЛЬНО сохраняй таджикские буквы: ғ, қ, ҳ, ҷ, ӣ, ӯ
2. Нумеруй тесты последовательно (1, 2, 3...)
3. Варианты ответов ТОЛЬКО: A, B, C, D (латинские буквы)
4. Если варианты в PDF: А), В), С), D) или а), б), в), г) - конвертируй в A, B, C, D
5. Сохраняй все даты, имена, события точно как в оригинале
6. НЕ добавляй правильные ответы (они будут позже)

Верни ТОЛЬКО валидный JSON, без ```json``` и текста.
"""
    
    print("Отправка запроса к Gemini API...")
    print("⏳ Это может занять несколько минут для большого PDF...")
    print("📊 Обработка документа...")
    
    # Отправляем запрос с отображением прогресса
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[prompt, pdf_file],
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            ),
        )
    except Exception as exc:
        print(f"❌ Ошибка при обращении к модели {MODEL_NAME}: {exc}")
        print("Проверьте доступные модели командой list_models.py")
        return []
    
    print("✅ Получен ответ от Gemini")
    print(f"📝 Размер ответа: {len(response.text)} символов")
    
    # Парсим JSON ответ
    try:
        print("🔄 Парсинг JSON ответа...")
        response_text = response.text.strip()
        
        # Убираем markdown форматирование
        print("🧹 Очистка форматирования...")
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.startswith('```'):
            response_text = response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        print("📦 Загрузка JSON данных...")
        data = json.loads(response_text)
        tests = data.get('tests', [])
        
        print(f"✅ Извлечено {len(tests)} тестов")
        
        # Добавляем поля для совместимости с форматом импорта
        print("🔧 Обработка тестов...")
        for i, test in enumerate(tests, 1):
            test['difficulty'] = 1
            test['original_test_id'] = test['number']
            test['correct_answer'] = ''  # Будет добавлено позже
            
            # Показываем прогресс каждые 50 тестов
            if i % 50 == 0:
                print(f"   Обработано {i}/{len(tests)} тестов...")
        
        print(f"✅ Все {len(tests)} тестов обработаны")
        return tests
        
    except json.JSONDecodeError as e:
        print(f"❌ Ошибка парсинга JSON: {e}")
        print(f"\nОтвет Gemini (первые 1000 символов):")
        print(response.text[:1000])
        print("\n...")
        
        # Сохраняем полный ответ для анализа
        with open('gemini_response_debug.txt', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print(f"Полный ответ сохранен в gemini_response_debug.txt")
        
        return []

def assign_topics_to_tests(tests):
    """
    Распределяет тесты по топикам истории
    """
    
    # Топики для истории (примерное распределение)
    topics_info = [
        {'title': 'Таърихи қадим', 'order': 1, 'start': 1, 'end': 80},
        {'title': 'Таърихи асрҳои миёна', 'order': 2, 'start': 81, 'end': 160},
        {'title': 'Таърихи нав', 'order': 3, 'start': 161, 'end': 240},
        {'title': 'Таърихи навтарин', 'order': 4, 'start': 241, 'end': 320},
        {'title': 'Таърихи Тоҷикистон', 'order': 5, 'start': 321, 'end': 400},
    ]
    
    topics_with_tasks = []
    
    for topic_info in topics_info:
        topic_tasks = []
        for test in tests:
            test_num = test['number']
            if topic_info['start'] <= test_num <= topic_info['end']:
                topic_tasks.append(test)
        
        if topic_tasks:
            topics_with_tasks.append({
                'title': topic_info['title'],
                'order': topic_info['order'],
                'tasks': topic_tasks
            })
    
    return topics_with_tasks

def main():
    pdf_path = "A2-34_History_tj 4.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ Файл не найден: {pdf_path}")
        print("\nПоместите файл A2-34_History_tj 4.pdf в текущую директорию")
        return
    
    # Извлекаем тесты
    tests = extract_history_tests(pdf_path)
    
    if not tests:
        print("❌ Не удалось извлечь тесты")
        return
    
    # Распределяем по топикам
    print("\n📂 Распределение тестов по топикам...")
    topics_with_tasks = assign_topics_to_tests(tests)
    print(f"✅ Тесты распределены по {len(topics_with_tasks)} топикам")
    
    # Формируем финальный JSON
    output_data = {
        'subject': 'Таърих',
        'topics': topics_with_tasks
    }
    
    # Сохраняем в файл
    output_file = 'history_tests_import.json'
    print(f"\n💾 Сохранение данных в {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    print("✅ Файл сохранен")
    
    print(f"\n{'='*60}")
    print(f"✅ Данные сохранены в {output_file}")
    print(f"{'='*60}")
    print(f"\nСтатистика:")
    print(f"- Предмет: {output_data['subject']}")
    print(f"- Топиков: {len(topics_with_tasks)}")
    for topic in topics_with_tasks:
        print(f"  - {topic['title']}: {len(topic['tasks'])} тестов")
    print(f"- Всего тестов: {sum(len(t['tasks']) for t in topics_with_tasks)}")
    print(f"\n⚠️  ВАЖНО: Правильные ответы НЕ добавлены!")
    print(f"Позже добавьте их с помощью скрипта add_answers.py")

if __name__ == '__main__':
    main()
