#!/usr/bin/env python3
"""
Скрипт для парсинга тестов по предмету Физика из Markdown файлов
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
    pattern = r'\\hline\s+(\d+)\s+&\s+([A-D])\s+\\\\'
    matches = re.findall(pattern, content)
    
    for num, answer in matches:
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
        
        # Проверяем специальный случай: \section*{256 Текст вопроса}
        section_match = re.match(r'^\\section\*\{(\d+)\s+(.+)\}$', line)
        if section_match:
            num = int(section_match.group(1))
            question_text = section_match.group(2).strip()
            i += 1
            
            # Собираем формулы и продолжение вопроса
            in_formula = False
            formula_content = ''
            while i < len(lines):
                curr_line = lines[i].strip()
                
                if re.match(r'^[AАa][)\)]', curr_line):
                    break
                
                if curr_line.startswith('$$'):
                    if not in_formula:
                        in_formula = True
                    else:
                        if formula_content.strip():
                            question_text += ' $$' + formula_content.strip() + '$$'
                        in_formula = False
                        formula_content = ''
                    i += 1
                    continue
                
                if in_formula:
                    formula_content += ' ' + curr_line
                    i += 1
                    continue
                
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
            if len(num_str) <= 3:
                num = int(num_str)
                question_text = match.group(2).strip()
                
                i += 1
                in_formula = False
                formula_content = ''
                
                while i < len(lines):
                    curr_line = lines[i].strip()
                    
                    # Пропускаем ссылки на изображения
                    if curr_line.startswith('![](') or 'cdn.mathpix.com' in curr_line:
                        i += 1
                        continue
                    
                    # Проверяем, не начались ли варианты ответов
                    if re.match(r'^[AАa][)\)]', curr_line) or re.match(r'^A\)', curr_line):
                        break
                    
                    # Пропускаем LaTeX команды
                    if curr_line.startswith('\\section') or curr_line.startswith('\\hline'):
                        i += 1
                        continue
                    
                    # Обработка математических формул
                    if curr_line.startswith('$$'):
                        if not in_formula:
                            in_formula = True
                            formula_content = ''
                        else:
                            if formula_content.strip():
                                question_text += ' $$' + formula_content.strip() + '$$'
                            in_formula = False
                            formula_content = ''
                        i += 1
                        continue
                    
                    if in_formula:
                        formula_content += ' ' + curr_line
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
        
        i += 1
    
    return all_tasks

def assign_topics_to_tasks(tasks):
    """Назначение топиков к тестам на основе номеров вопросов"""
    topics_data = [
        {
            'title': 'Механика',
            'order': 1,
            'start': 1,
            'end': 189
        },
        {
            'title': 'Физикаи молекулавӣ ва термодинамика',
            'order': 2,
            'start': 190,
            'end': 255
        },
        {
            'title': 'Электродинамика',
            'order': 3,
            'start': 256,
            'end': 381
        },
        {
            'title': 'Оптика',
            'order': 4,
            'start': 382,
            'end': 431
        },
        {
            'title': 'Физикаи атом ва ядрои атом',
            'order': 5,
            'start': 432,
            'end': 507
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
    test_file = 'A4-15_Physics_tj.md'
    key_file = 'A4-15_Physics_tj_key.md'
    
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
        'subject': 'Физика',
        'topics': topics_with_tasks
    }
    
    # Сохраняем в JSON файл
    output_file = 'physics_tests_import.json'
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
