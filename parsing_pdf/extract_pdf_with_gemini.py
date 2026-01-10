#!/usr/bin/env python3
"""
Скрипт для извлечения тестов из PDF файлов с помощью Gemini API
и конвертации в нужный формат для импорта в БД
"""

import os
import sys
import json
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

def extract_tests_from_pdf(pdf_path, subject_name, topics_info):
    """
    Извлекает тесты из PDF файла с помощью Gemini API
    
    Args:
        pdf_path: путь к PDF файлу
        subject_name: название предмета
        topics_info: список словарей с информацией о топиках
                     [{'title': 'Название', 'start': 1, 'end': 50}, ...]
    
    Returns:
        dict: данные в формате для импорта
    """
    
    print(f"Загрузка PDF файла: {pdf_path}")
    
    # Загружаем PDF файл
    pdf_file = genai.upload_file(pdf_path)
    print(f"✅ Файл загружен: {pdf_file.display_name}")
    
    # Создаем модель
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Промпт для извлечения тестов
    prompt = f"""
Извлеки все тесты из этого PDF файла по предмету "{subject_name}".

КРИТИЧЕСКИ ВАЖНО:
- Текст на ТАДЖИКСКОМ языке (кириллица с буквами ғ, қ, ҳ, ҷ, ӣ, ӯ)
- Сохраняй ВСЕ таджикские буквы ТОЧНО как в оригинале
- Верни результат ТОЛЬКО в формате JSON, без дополнительного текста

Формат JSON:
{{
  "tests": [
    {{
      "number": 1,
      "question": "Текст вопроса на таджикском (сохрани все формулы в LaTeX)",
      "options": {{
        "A": "Вариант A на таджикском",
        "B": "Вариант B на таджикском",
        "C": "Вариант C на таджикском",
        "D": "Вариант D на таджикском"
      }}
    }},
    ...
  ]
}}

Правила:
1. ОБЯЗАТЕЛЬНО сохраняй таджикские буквы: ғ, қ, ҳ, ҷ, ӣ, ӯ
2. Сохраняй математические формулы в LaTeX: $x^2$, $$\\frac{{a}}{{b}}$$
3. Нумеруй тесты последовательно (1, 2, 3...)
4. Варианты ответов: A, B, C, D (латинские буквы)
5. Если есть изображения/графики - опиши их в вопросе
6. НЕ добавляй правильные ответы (они будут добавлены позже)
7. Если в PDF варианты обозначены как А), В), С), D) или а), б), в), г) - конвертируй в A, B, C, D

Верни ТОЛЬКО валидный JSON, без ```json``` и без дополнительного текста.
"""
    
    print("Отправка запроса к Gemini API...")
    response = model.generate_content([pdf_file, prompt])
    
    print("✅ Получен ответ от Gemini")
    
    # Парсим JSON ответ
    try:
        # Убираем markdown форматирование если есть
        response_text = response.text.strip()
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.startswith('```'):
            response_text = response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        data = json.loads(response_text)
        tests = data.get('tests', [])
        
        print(f"✅ Извлечено {len(tests)} тестов")
        
        return tests
        
    except json.JSONDecodeError as e:
        print(f"❌ Ошибка парсинга JSON: {e}")
        print(f"Ответ Gemini:\n{response.text[:500]}...")
        return []

def extract_answers_from_pdf(pdf_path):
    """
    Извлекает правильные ответы из PDF файла с ключами
    
    Args:
        pdf_path: путь к PDF файлу с ответами
    
    Returns:
        dict: словарь {номер_теста: правильный_ответ}
    """
    
    print(f"Загрузка PDF файла с ответами: {pdf_path}")
    
    pdf_file = genai.upload_file(pdf_path)
    print(f"✅ Файл загружен: {pdf_file.display_name}")
    
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = """
Извлеки все правильные ответы из этого PDF файла.

ВАЖНО: Верни результат ТОЛЬКО в формате JSON, без дополнительного текста.

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
3. Верни ТОЛЬКО валидный JSON

Верни ТОЛЬКО валидный JSON, без markdown форматирования.
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
        print(f"Ответ Gemini:\n{response.text[:500]}...")
        return {}

def combine_tests_and_answers(tests, answers, topics_info):
    """
    Объединяет тесты с ответами и распределяет по топикам
    
    Args:
        tests: список тестов
        answers: словарь с ответами
        topics_info: информация о топиках
    
    Returns:
        dict: данные в формате для импорта
    """
    
    # Добавляем правильные ответы к тестам
    for test in tests:
        test_num = test['number']
        test['correct_answer'] = answers.get(test_num, '')
        test['difficulty'] = 1
        test['original_test_id'] = test_num
    
    # Распределяем тесты по топикам
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
    """
    Пример использования скрипта
    """
    
    # Пример: извлечение тестов по биологии
    subject_name = "Биология"
    
    # Определяем топики
    topics_info = [
        {'title': 'Ботаника', 'order': 1, 'start': 1, 'end': 100},
        {'title': 'Зоология', 'order': 2, 'start': 101, 'end': 200},
        {'title': 'Анатомия', 'order': 3, 'start': 201, 'end': 300},
    ]
    
    # Пути к файлам (замените на реальные)
    tests_pdf = "biology_tests.pdf"
    answers_pdf = "biology_answers.pdf"
    
    # Проверяем существование файлов
    if not os.path.exists(tests_pdf):
        print(f"❌ Файл не найден: {tests_pdf}")
        print("\nИспользование:")
        print("1. Поместите PDF файл с тестами в текущую директорию")
        print("2. Поместите PDF файл с ответами в текущую директорию")
        print("3. Установите GEMINI_API_KEY: export GEMINI_API_KEY='your-key'")
        print("4. Запустите скрипт: python extract_pdf_with_gemini.py")
        return
    
    # Извлекаем тесты
    tests = extract_tests_from_pdf(tests_pdf, subject_name, topics_info)
    
    if not tests:
        print("❌ Не удалось извлечь тесты")
        return
    
    # Извлекаем ответы
    answers = extract_answers_from_pdf(answers_pdf)
    
    if not answers:
        print("⚠️  Не удалось извлечь ответы, продолжаем без них")
    
    # Объединяем данные
    topics_with_tasks = combine_tests_and_answers(tests, answers, topics_info)
    
    # Формируем финальный JSON
    output_data = {
        'subject': subject_name,
        'topics': topics_with_tasks
    }
    
    # Сохраняем в файл
    output_file = f'{subject_name.lower()}_tests_import.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Данные сохранены в {output_file}")
    print(f"\nСтатистика:")
    print(f"- Предмет: {output_data['subject']}")
    print(f"- Топиков: {len(topics_with_tasks)}")
    for topic in topics_with_tasks:
        print(f"  - {topic['title']}: {len(topic['tasks'])} тестов")
    print(f"- Всего тестов: {sum(len(t['tasks']) for t in topics_with_tasks)}")

if __name__ == '__main__':
    main()
