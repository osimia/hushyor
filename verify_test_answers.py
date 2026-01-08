#!/usr/bin/env python3
"""
Скрипт для проверки правильности соответствия тестов и ключей ответов
"""

import json
import sys

def verify_answers(json_file, verbose=False):
    """Проверяет, что у каждого теста есть правильный ключ ответа"""
    
    print(f"📖 Чтение данных из: {json_file}")
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    total_tests = 0
    tests_with_answers = 0
    tests_without_answers = []
    invalid_answers = []
    
    print("\n🔍 Проверка тестов...\n")
    
    for topic in data['topics']:
        topic_title = topic['title']
        tasks = topic['tasks']
        
        print(f"📁 {topic_title}")
        
        topic_total = len(tasks)
        topic_with_answers = 0
        
        for task in tasks:
            total_tests += 1
            test_id = task.get('original_test_id')
            question = task.get('question', '')[:50] + '...'
            correct_answer = task.get('correct_answer', '')
            options = task.get('options', {})
            
            # Проверяем наличие ответа
            if not correct_answer:
                tests_without_answers.append({
                    'id': test_id,
                    'topic': topic_title,
                    'question': question
                })
                if verbose:
                    print(f"  ❌ Тест #{test_id}: НЕТ ОТВЕТА")
            else:
                # Проверяем, что ответ является одним из вариантов A, B, C, D
                if correct_answer not in ['A', 'B', 'C', 'D']:
                    invalid_answers.append({
                        'id': test_id,
                        'topic': topic_title,
                        'answer': correct_answer,
                        'question': question
                    })
                    if verbose:
                        print(f"  ⚠️  Тест #{test_id}: НЕВЕРНЫЙ ФОРМАТ ОТВЕТА '{correct_answer}'")
                else:
                    # Проверяем, что вариант ответа существует в options
                    if correct_answer not in options:
                        invalid_answers.append({
                            'id': test_id,
                            'topic': topic_title,
                            'answer': correct_answer,
                            'question': question,
                            'reason': 'Вариант ответа не найден в options'
                        })
                        if verbose:
                            print(f"  ⚠️  Тест #{test_id}: Вариант '{correct_answer}' не найден в options")
                    else:
                        tests_with_answers += 1
                        topic_with_answers += 1
                        if verbose:
                            print(f"  ✅ Тест #{test_id}: {correct_answer}) {options[correct_answer][:30]}...")
        
        print(f"  Итого: {topic_with_answers}/{topic_total} тестов с правильными ответами\n")
    
    # Итоговая статистика
    print("=" * 70)
    print("📊 ИТОГОВАЯ СТАТИСТИКА:")
    print("=" * 70)
    print(f"Всего тестов: {total_tests}")
    print(f"✅ Тестов с правильными ответами: {tests_with_answers} ({tests_with_answers/total_tests*100:.1f}%)")
    print(f"❌ Тестов без ответов: {len(tests_without_answers)}")
    print(f"⚠️  Тестов с неверными ответами: {len(invalid_answers)}")
    
    # Детальная информация о проблемах
    if tests_without_answers:
        print("\n" + "=" * 70)
        print("❌ ТЕСТЫ БЕЗ ОТВЕТОВ:")
        print("=" * 70)
        for test in tests_without_answers:
            print(f"  Тест #{test['id']} ({test['topic']})")
            print(f"    Вопрос: {test['question']}")
    
    if invalid_answers:
        print("\n" + "=" * 70)
        print("⚠️  ТЕСТЫ С НЕВЕРНЫМИ ОТВЕТАМИ:")
        print("=" * 70)
        for test in invalid_answers:
            print(f"  Тест #{test['id']} ({test['topic']})")
            print(f"    Ответ: {test['answer']}")
            print(f"    Вопрос: {test['question']}")
            if 'reason' in test:
                print(f"    Причина: {test['reason']}")
    
    # Проверка последовательности ID
    print("\n" + "=" * 70)
    print("🔢 ПРОВЕРКА ПОСЛЕДОВАТЕЛЬНОСТИ ID:")
    print("=" * 70)
    
    all_ids = []
    for topic in data['topics']:
        for task in topic['tasks']:
            all_ids.append(task.get('original_test_id'))
    
    all_ids.sort()
    
    # Находим пропущенные ID
    if all_ids:
        min_id = min(all_ids)
        max_id = max(all_ids)
        expected_ids = set(range(min_id, max_id + 1))
        actual_ids = set(all_ids)
        missing_ids = sorted(expected_ids - actual_ids)
        
        print(f"Диапазон ID: {min_id} - {max_id}")
        print(f"Найдено ID: {len(actual_ids)}")
        print(f"Ожидалось ID: {len(expected_ids)}")
        
        if missing_ids:
            print(f"\n⚠️  Пропущенные ID ({len(missing_ids)} штук):")
            # Группируем последовательные ID
            groups = []
            start = missing_ids[0]
            end = missing_ids[0]
            
            for i in range(1, len(missing_ids)):
                if missing_ids[i] == end + 1:
                    end = missing_ids[i]
                else:
                    if start == end:
                        groups.append(str(start))
                    else:
                        groups.append(f"{start}-{end}")
                    start = missing_ids[i]
                    end = missing_ids[i]
            
            if start == end:
                groups.append(str(start))
            else:
                groups.append(f"{start}-{end}")
            
            print(f"  {', '.join(groups)}")
        else:
            print("✅ Все ID последовательны, пропусков нет")
        
        # Проверка дубликатов
        duplicates = [id for id in all_ids if all_ids.count(id) > 1]
        if duplicates:
            print(f"\n⚠️  Найдены дубликаты ID: {sorted(set(duplicates))}")
        else:
            print("✅ Дубликатов ID не найдено")
    
    print("\n" + "=" * 70)
    
    # Возвращаем код выхода
    if tests_without_answers or invalid_answers:
        return 1
    return 0

if __name__ == '__main__':
    verbose = '--verbose' in sys.argv or '-v' in sys.argv
    json_file = 'math_tests_import.json'
    
    exit_code = verify_answers(json_file, verbose=verbose)
    
    if exit_code == 0:
        print("\n✅ ВСЕ ТЕСТЫ ПРОШЛИ ПРОВЕРКУ!")
    else:
        print("\n⚠️  ОБНАРУЖЕНЫ ПРОБЛЕМЫ. Проверьте детали выше.")
    
    sys.exit(exit_code)
