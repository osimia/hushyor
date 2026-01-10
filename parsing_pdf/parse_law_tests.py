#!/usr/bin/env python3
"""
Скрипт для парсинга тестов по предмету Ҳуқуқ (Право) из Markdown файлов
и подготовки данных для импорта в БД Django
"""

import re
import json

def parse_answer_key(key_file_path):
    """Парсинг файла с ответами"""
    answers = {}
    
    with open(key_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Находим все пары номер-ответ в таблицах
    # Учитываем разные форматы: $\mathbf{1 0}$ и просто 1
    # Паттерн 1: с $\mathbf{...}$
    pattern1 = r'\\hline\s+\$\\mathbf\{(\d+(?:\s+\d)?)\}\$\s+&\s+([A-D])\s+\\\\'
    # Паттерн 2: просто числа
    pattern2 = r'\\hline\s+(\d+)\s+&\s+([A-D])\s+\\\\'
    
    matches1 = re.findall(pattern1, content)
    matches2 = re.findall(pattern2, content)
    
    for num, answer in matches1:
        # Убираем пробелы из номера (например "1 0" -> "10")
        num_clean = num.replace(' ', '')
        answers[int(num_clean)] = answer
    
    for num, answer in matches2:
        answers[int(num)] = answer
    
    return answers

def parse_tests(test_file_path, answers):
    """Парсинг файла с тестами"""
    with open(test_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    all_tasks = []
    lines = content.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Проверяем специальный случай: \section*{105 Текст вопроса}
        section_match = re.match(r'^\\section\*\{(\d+)\s+(.+)\}$', line)
        if section_match:
            num = int(section_match.group(1))
            question_text = section_match.group(2).strip()
            i += 1
            
            # Собираем продолжение вопроса
            while i < len(lines):
                curr_line = lines[i].strip()
                
                # Проверяем, не начались ли варианты ответов
                if re.match(r'^[AАa][)\)]', curr_line):
                    break
                
                # Проверяем, не началось ли следующее section
                if curr_line.startswith('\\section'):
                    break
                
                # Проверяем, не началось ли следующее питание
                next_q = re.match(r'^(\d+)\s', curr_line)
                if next_q and len(next_q.group(1)) <= 3:
                    break
                
                if curr_line and not curr_line.startswith('\\'):
                    question_text += ' ' + curr_line
                
                i += 1
            
            # Собираем варианты ответов
            options = {}
            option_order = ['A', 'B', 'C', 'D']
            letter_variants = {
                'A': r'[AАa]',
                'B': r'[BВb]',
                'C': r'[CСc]',
                'D': r'[Dd]'
            }
            
            for expected_letter in option_order:
                if i >= len(lines):
                    break
                
                curr_line = lines[i].strip()
                pattern = r'^' + letter_variants[expected_letter] + r'[)\)]\s*(.+)$'
                option_match = re.match(pattern, curr_line)
                
                if option_match:
                    option_text = option_match.group(1).strip()
                    options[expected_letter] = option_text
                    i += 1
                else:
                    break
            
            if len(options) == 4:
                correct_answer = answers.get(num, '')
                task = {
                    'original_test_id': num,
                    'question': question_text.strip(),
                    'options': options,
                    'correct_answer': correct_answer,
                    'difficulty': 1
                }
                all_tasks.append(task)
                continue
        
        # Обычный случай: номер вопроса в начале строки
        match = re.match(r'^(\d+)\s+(.*)$', line)
        if match and not line.startswith('\\'):
            num_str = match.group(1)
            # Проверяем, что это действительно номер вопроса (1-3 цифры)
            if len(num_str) <= 3:
                num = int(num_str)
                question_text = match.group(2).strip()
                
                # Собираем полный текст вопроса (может быть многострочным)
                i += 1
                
                while i < len(lines):
                    curr_line = lines[i].strip()
                    
                    # Проверяем, не начались ли варианты ответов
                    if re.match(r'^[AАa][)\)]', curr_line) or re.match(r'^A\)', curr_line):
                        break
                    
                    # Пропускаем LaTeX команды и пустые строки
                    if curr_line.startswith('\\section') or curr_line.startswith('\\hline'):
                        i += 1
                        continue
                    
                    # Проверяем, не началось ли новое питание
                    next_q = re.match(r'^(\d+)\s', curr_line)
                    if next_q and len(next_q.group(1)) <= 3:
                        break
                    
                    # Добавляем текст к вопросу
                    if curr_line and not curr_line.startswith('\\'):
                        question_text += ' ' + curr_line
                    
                    i += 1
                
                # Собираем варианты ответов
                options = {}
                option_order = ['A', 'B', 'C', 'D']
                
                # Маппинг латинских и кириллических букв
                letter_variants = {
                    'A': r'[AАa]',
                    'B': r'[BВb]',
                    'C': r'[CСc]',
                    'D': r'[Dd]'
                }
                
                for expected_letter in option_order:
                    if i >= len(lines):
                        break
                    
                    curr_line = lines[i].strip()
                    # Ищем вариант с учетом кириллических и латинских букв
                    pattern = r'^' + letter_variants[expected_letter] + r'[)\)]\s*(.+)$'
                    option_match = re.match(pattern, curr_line)
                    
                    if option_match:
                        option_text = option_match.group(1).strip()
                        options[expected_letter] = option_text
                        i += 1
                    else:
                        break
                
                # Если нашли все 4 варианта
                if len(options) == 4:
                    correct_answer = answers.get(num, '')
                    
                    task = {
                        'original_test_id': num,
                        'question': question_text.strip(),
                        'options': options,
                        'correct_answer': correct_answer,
                        'difficulty': 1
                    }
                    all_tasks.append(task)
                    continue
        
        i += 1
    
    return all_tasks

def assign_topics_to_tasks(tasks):
    """Назначение топиков к тестам на основе номеров вопросов"""
    topics_data = [
        {
            'title': 'Асосҳои назариявии ҳуқуқ ва давлат',
            'order': 1,
            'start': 1,
            'end': 60
        },
        {
            'title': 'Ҳуқуқи конститутсионӣ',
            'order': 2,
            'start': 61,
            'end': 120
        },
        {
            'title': 'Ҳуқуқи граждани (маданӣ)',
            'order': 3,
            'start': 121,
            'end': 180
        },
        {
            'title': 'Ҳуқуқи оилавӣ',
            'order': 4,
            'start': 181,
            'end': 220
        },
        {
            'title': 'Ҳуқуқи меҳнатӣ',
            'order': 5,
            'start': 221,
            'end': 260
        },
        {
            'title': 'Ҳуқуқи маъмурӣ ва ҷиноятӣ',
            'order': 6,
            'start': 261,
            'end': 336
        }
    ]
    
    # Группируем тесты по топикам
    topics_with_tasks = []
    
    for topic_info in topics_data:
        topic_tasks = []
        for task in tasks:
            test_id = task['original_test_id']
            if topic_info['start'] <= test_id <= topic_info['end']:
                topic_tasks.append(task)
        
        if topic_tasks:
            topics_with_tasks.append({
                'title': topic_info['title'],
                'order': topic_info['order'],
                'tasks': topic_tasks
            })
    
    return topics_with_tasks

def main():
    test_file = 'A3-4_Law_tj 4.md'
    key_file = 'A3-4_Law_tj_key 4.md'
    
    print("Парсинг ответов...")
    answers = parse_answer_key(key_file)
    print(f"Найдено {len(answers)} ответов")
    
    print("\nПарсинг тестов...")
    tasks = parse_tests(test_file, answers)
    print(f"Найдено {len(tasks)} тестов")
    
    print("\nНазначение топиков...")
    topics_with_tasks = assign_topics_to_tasks(tasks)
    
    # Формируем финальный JSON
    output_data = {
        'subject': 'Ҳуқуқ',
        'topics': topics_with_tasks
    }
    
    # Сохраняем в JSON файл
    output_file = 'law_tests_import.json'
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
