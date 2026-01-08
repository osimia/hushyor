#!/usr/bin/env python3
"""
Скрипт для парсингу математичних тестів з Markdown файлів
та підготовки даних для імпорту в БД Django
"""

import re
import json

def parse_answer_key(key_file_path):
    """Парсинг файлу з відповідями"""
    answers = {}
    
    with open(key_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Знаходимо всі пари номер-відповідь у таблицях
    pattern = r'\\hline\s+(\d+)\s+&\s+([A-D])\s+\\\\'
    matches = re.findall(pattern, content)
    
    for num, answer in matches:
        answers[int(num)] = answer
    
    return answers

def parse_tests(test_file_path, answers):
    """Парсинг файлу з тестами"""
    with open(test_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Визначаємо топіки за заголовками
    topics = []
    current_topic = None
    current_topic_start = 0
    
    # Знаходимо всі заголовки топіків
    topic_pattern = r'\\section\*\{([^}]+)\}'
    topic_matches = list(re.finditer(topic_pattern, content))
    
    # Визначаємо основні топіки (пропускаємо перші 2 - це заголовки документа)
    main_topics = []
    for i, match in enumerate(topic_matches):
        title = match.group(1)
        # Пропускаємо заголовки документа та питання
        if 'НАМУНАИ' in title or 'саволу масъалахои' in title or 'САВОЛУ МАСЪАЛАХО' in title:
            continue
        if 'Хисоб кунед' in title or 'Қимати ифодаро' in title or 'Ифодаро сода' in title:
            continue
        if 'Решаи муодиларо' in title or 'Муодиларо хал' in title or 'Узви номаълуми' in title:
            continue
        if 'Суммаи решахои' in title or 'Миёнаи геометрии' in title or 'Миёнаи арифметикии' in title:
            continue
        if 'Ададхои' in title and 'халли системаи' in title:
            continue
        if 'Тасдикоти дурустро' in title or 'Тасдикоти нодурустро' in title or 'Тасдиқоти дурустро' in title:
            continue
        
        main_topics.append({
            'title': title,
            'start': match.start(),
            'end': topic_matches[i+1].start() if i+1 < len(topic_matches) else len(content)
        })
    
    # Парсимо питання
    all_tasks = []
    
    lines = content.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Проверяем специальный случай: \section*{49 Текст вопроса}
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
                        # Начало формулы
                        in_formula = True
                    else:
                        # Конец формулы - добавляем в формате LaTeX
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
        match = re.match(r'^(\d+)\s*(.*)$', line)
        if match and not line.startswith('\\'):
            num_str = match.group(1)
            # Проверяем, что это действительно номер вопроса (1-3 цифры)
            if len(num_str) <= 3:
                num = int(num_str)
                question_text = match.group(2).strip()
                
                # Проверяем, нет ли варианта ответа на той же строке
                if re.search(r'[AАa][)\)]\s*\d+', question_text):
                    # Варианты ответов начинаются на той же строке
                    parts = re.split(r'([AАa][)\)])', question_text, 1)
                    if len(parts) >= 3:
                        question_text = parts[0].strip()
                        # Восстанавливаем строку с вариантом A
                        lines[i] = parts[1] + parts[2]
                
                # Збираємо повний текст питання (може бути багаторядковим)
                i += 1
                in_formula = False
                formula_content = ''
                
                while i < len(lines):
                    curr_line = lines[i].strip()
                    
                    # Пропускаем ссылки на изображения
                    if curr_line.startswith('![](') or 'cdn.mathpix.com' in curr_line:
                        i += 1
                        continue
                    
                    # Перевіряємо, чи не почалися варіанти відповідей
                    if re.match(r'^[AАa][)\)]', curr_line) or re.match(r'^A\)', curr_line):
                        break
                    
                    # Пропускаємо LaTeX команди та порожні рядки
                    if curr_line.startswith('\\section') or curr_line.startswith('\\hline'):
                        i += 1
                        continue
                    
                    # Обробка математичних формул
                    if curr_line.startswith('$$'):
                        if not in_formula:
                            # Начало формулы
                            in_formula = True
                            formula_content = ''
                        else:
                            # Конец формулы - добавляем в формате LaTeX
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
                    
                    # Перевіряємо, чи не почалося нове питання
                    next_q = re.match(r'^(\d+)\s', curr_line)
                    if next_q and len(next_q.group(1)) <= 3:
                        break
                    
                    # Додаємо текст до питання
                    if curr_line and not curr_line.startswith('\\'):
                        question_text += ' ' + curr_line
                    
                    i += 1
                
                # Збираємо варіанти відповідей
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
                
                # Якщо знайшли всі 4 варіанти
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
    """Призначення топіків до тестів на основі номерів питань"""
    topics_data = [
        {
            'title': 'АМАЛХО БО АДАДХОИ РАТСИОНАЛЙ ВА ИРРАТСИОНАЛЙ',
            'order': 1,
            'start': 1,
            'end': 48
        },
        {
            'title': 'РЕШАХОИ КВАДРАТЙ',
            'order': 2,
            'start': 49,
            'end': 72
        },
        {
            'title': 'ИФОДАХОИ РАТСИОНАЛЙ ВА ИРРАТСИОНАЛЙ',
            'order': 3,
            'start': 73,
            'end': 93
        },
        {
            'title': 'ТАСДИҚОТХОИ АЛГЕБРАВЙ',
            'order': 4,
            'start': 94,
            'end': 111
        },
        {
            'title': 'МУОДИЛА ВА СИСТЕМАИ МУОДИЛАХОИ РАТСИОНАЛЙ ВА ИРРАТСИОНАЛЙ',
            'order': 5,
            'start': 112,
            'end': 162
        },
        {
            'title': 'МАСЪАЛАХОИ МАТНЙ',
            'order': 6,
            'start': 163,
            'end': 999  # До кінця
        }
    ]
    
    # Групуємо тести по топіках
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
    test_file = 'A2-12_Math_tj.md'
    key_file = 'A2-12_Math_tj_key.md'
    
    print("Парсинг відповідей...")
    answers = parse_answer_key(key_file)
    print(f"Знайдено {len(answers)} відповідей")
    
    print("\nПарсинг тестів...")
    tasks = parse_tests(test_file, answers)
    print(f"Знайдено {len(tasks)} тестів")
    
    print("\nПризначення топіків...")
    topics_with_tasks = assign_topics_to_tasks(tasks)
    
    # Формуємо фінальний JSON
    output_data = {
        'subject': 'Математика',
        'topics': topics_with_tasks
    }
    
    # Зберігаємо в JSON файл
    output_file = 'math_tests_import.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Дані збережено в {output_file}")
    print(f"\nСтатистика:")
    print(f"- Предмет: {output_data['subject']}")
    print(f"- Топіків: {len(topics_with_tasks)}")
    for topic in topics_with_tasks:
        print(f"  - {topic['title']}: {len(topic['tasks'])} тестів")
    print(f"- Всього тестів: {sum(len(t['tasks']) for t in topics_with_tasks)}")

if __name__ == '__main__':
    main()
