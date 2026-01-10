# Извлечение тестов из PDF с помощью Gemini API

## Установка зависимостей

```bash
pip install google-generativeai
```

## Настройка API ключа

1. Получите API ключ на https://aistudio.google.com/app/apikey
2. Установите переменную окружения:

**Windows (PowerShell):**
```powershell
$env:GEMINI_API_KEY="your-api-key-here"
```

**Linux/Mac:**
```bash
export GEMINI_API_KEY="your-api-key-here"
```

## Использование скрипта

### Базовый пример

```python
from extract_pdf_with_gemini import extract_tests_from_pdf, extract_answers_from_pdf, combine_tests_and_answers

# 1. Определите предмет и топики
subject_name = "Биология"
topics_info = [
    {'title': 'Ботаника', 'order': 1, 'start': 1, 'end': 100},
    {'title': 'Зоология', 'order': 2, 'start': 101, 'end': 200},
]

# 2. Извлеките тесты из PDF
tests = extract_tests_from_pdf("biology_tests.pdf", subject_name, topics_info)

# 3. Извлеките ответы из PDF с ключами
answers = extract_answers_from_pdf("biology_answers.pdf")

# 4. Объедините данные
topics_with_tasks = combine_tests_and_answers(tests, answers, topics_info)

# 5. Сохраните в JSON
import json
output_data = {'subject': subject_name, 'topics': topics_with_tasks}
with open('biology_tests_import.json', 'w', encoding='utf-8') as f:
    json.dump(output_data, f, ensure_ascii=False, indent=2)
```

### Запуск готового скрипта

```bash
python extract_pdf_with_gemini.py
```

## Формат вывода

Скрипт создает JSON файл в формате:

```json
{
  "subject": "Биология",
  "topics": [
    {
      "title": "Ботаника",
      "order": 1,
      "tasks": [
        {
          "number": 1,
          "question": "Текст вопроса с формулами $x^2$",
          "options": {
            "A": "Вариант A",
            "B": "Вариант B",
            "C": "Вариант C",
            "D": "Вариант D"
          },
          "correct_answer": "A",
          "difficulty": 1,
          "original_test_id": 1
        }
      ]
    }
  ]
}
```

## Особенности

✅ **Сохраняет формулы в LaTeX формате** - все математические выражения сохраняются как `$formula$` или `$$formula$$`

✅ **Поддерживает таджикский язык** - корректно обрабатывает кириллицу

✅ **Автоматическое распределение по топикам** - тесты автоматически группируются по заданным диапазонам

✅ **Обработка изображений** - если в PDF есть графики, Gemini их описывает в тексте

## Ограничения Gemini API

- **Размер файла**: до 20 МБ для PDF
- **Бесплатный лимит**: 15 запросов в минуту
- **Качество**: зависит от качества PDF (лучше работает с текстовыми PDF, а не сканами)

## Советы по использованию

1. **Разделите большие PDF**: если файл содержит >200 тестов, лучше разделить на части
2. **Проверьте результат**: всегда проверяйте извлеченные данные вручную
3. **Используйте качественные PDF**: текстовые PDF работают лучше, чем отсканированные изображения
4. **Сохраняйте промежуточные результаты**: Gemini API может давать разные результаты при повторных запросах

## Пример для реального использования

```python
# Для предмета "Химия"
subject_name = "Химия"
topics_info = [
    {'title': 'Неорганическая химия', 'order': 1, 'start': 1, 'end': 150},
    {'title': 'Органическая химия', 'order': 2, 'start': 151, 'end': 300},
    {'title': 'Физическая химия', 'order': 3, 'start': 301, 'end': 400},
]

tests = extract_tests_from_pdf("chemistry_tests.pdf", subject_name, topics_info)
answers = extract_answers_from_pdf("chemistry_answers.pdf")
topics = combine_tests_and_answers(tests, answers, topics_info)

# Сохранить
import json
with open('chemistry_tests_import.json', 'w', encoding='utf-8') as f:
    json.dump({'subject': subject_name, 'topics': topics}, f, ensure_ascii=False, indent=2)
```

## Импорт в базу данных

После создания JSON файла используйте стандартный скрипт импорта:

```bash
python parsing_pdf/import_chemistry_tests.py
```
