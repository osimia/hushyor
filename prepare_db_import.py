#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для подготовки данных тестов для импорта в базу данных Django
Объединяет вопросы с правильными ответами
"""

import json
from pathlib import Path


def prepare_for_database():
    """
    Читает тесты и ответы, объединяет их и готовит для импорта в БД
    """
    # Пути к файлам
    tests_file = Path("test_database_clean.json")
    answers_file = Path("answer_keys.json")
    output_file = Path("tests_for_import.json")
    
    print("📖 Читаю файлы...")
    
    # Читаем тесты
    with open(tests_file, 'r', encoding='utf-8') as f:
        tests = json.load(f)
    
    # Читаем ответы
    with open(answers_file, 'r', encoding='utf-8') as f:
        answers = json.load(f)
    
    print(f"📊 Загружено тестов: {len(tests)}")
    print(f"📊 Загружено ответов: {len(answers)}")
    
    # Подготовка данных для БД
    prepared_tests = []
    missing_answers = []
    
    for test in tests:
        test_id = str(test['id'])
        
        # Проверяем наличие ответа
        if test_id not in answers:
            missing_answers.append(test_id)
            correct_answer = None
        else:
            correct_answer = answers[test_id]
        
        # Формируем структуру для БД согласно Django модели
        db_record = {
            "model": "tojiki.question",  # app_name.model_name
            "pk": test['id'],
            "fields": {
                "category": test['category'],
                "question_text": test['question_text'],
                "option_a": test['options'].get('A', ''),
                "option_b": test['options'].get('B', ''),
                "option_c": test['options'].get('C', ''),
                "option_d": test['options'].get('D', ''),
                "correct_answer": correct_answer,
                "is_poetry": test.get('is_poetry', False),
                # Поля для matching вопросов (если есть)
                "matching_left_1": test['matching_options'].get('1', '') if test['matching_options'] else '',
                "matching_left_2": test['matching_options'].get('2', '') if test['matching_options'] else '',
                "matching_left_3": test['matching_options'].get('3', '') if test['matching_options'] else '',
                "matching_left_4": test['matching_options'].get('4', '') if test['matching_options'] else '',
                "matching_right_a": test['matching_options'].get('A', '') if test['matching_options'] else '',
                "matching_right_b": test['matching_options'].get('B', '') if test['matching_options'] else '',
                "matching_right_c": test['matching_options'].get('C', '') if test['matching_options'] else '',
                "matching_right_d": test['matching_options'].get('D', '') if test['matching_options'] else '',
            }
        }
        
        prepared_tests.append(db_record)
    
    # Сохраняем в файл для импорта
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(prepared_tests, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Подготовка завершена!")
    print(f"📝 Всего тестов обработано: {len(prepared_tests)}")
    print(f"💾 Сохранено в: {output_file}")
    
    if missing_answers:
        print(f"\n⚠️  Тесты без ответов ({len(missing_answers)}):")
        print(f"   ID: {', '.join(missing_answers[:20])}")
        if len(missing_answers) > 20:
            print(f"   ... и еще {len(missing_answers) - 20}")
    
    # Статистика по категориям
    categories = {}
    for test in tests:
        cat = test['category']
        categories[cat] = categories.get(cat, 0) + 1
    
    print(f"\n📊 Статистика по категориям:")
    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"   {cat}: {count}")
    
    # Пример первого теста
    print(f"\n📝 Пример первого теста:")
    if prepared_tests:
        example = prepared_tests[0]
        print(f"   ID: {example['pk']}")
        print(f"   Категория: {example['fields']['category']}")
        print(f"   Вопрос: {example['fields']['question_text'][:80]}...")
        print(f"   Варианты:")
        print(f"     A: {example['fields']['option_a']}")
        print(f"     B: {example['fields']['option_b']}")
        print(f"     C: {example['fields']['option_c']}")
        print(f"     D: {example['fields']['option_d']}")
        print(f"   Правильный ответ: {example['fields']['correct_answer']}")
    
    return prepared_tests


if __name__ == "__main__":
    prepare_for_database()
