#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для импорта тестов в Django БД
Адаптирован под модели: Subject, Topic, Task
"""

import json
import os
import sys
import django

# Настройка Django окружения
sys.path.append('/home/osimi/Рабочий стол/projects/hushyor')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hushyor.settings')
django.setup()

from core.models import Subject, Topic, Task


def import_tests():
    """
    Импортирует тесты из JSON файла в Django БД
    """
    # Пути к файлам
    tests_file = "test_database_fixed.json"  # Используем файл с исправленными категориями
    answers_file = "answer_keys.json"
    
    print("📖 Читаю файлы...")
    
    # Читаем тесты
    with open(tests_file, 'r', encoding='utf-8') as f:
        tests = json.load(f)
    
    # Читаем ответы
    with open(answers_file, 'r', encoding='utf-8') as f:
        answers = json.load(f)
    
    print(f"📊 Загружено тестов: {len(tests)}")
    print(f"📊 Загружено ответов: {len(answers)}")
    
    # 1. Создаем или получаем Subject "Забони тоҷикӣ"
    subject, created = Subject.objects.get_or_create(
        title="Забони тоҷикӣ",
        defaults={
            'icon': '📚',
            'color': '#4CAF50'
        }
    )
    if created:
        print(f"✅ Создан Subject: {subject.title}")
    else:
        print(f"📌 Subject уже существует: {subject.title}")
    
    # 2. Собираем уникальные категории и создаем Topics
    categories = {}
    for test in tests:
        cat = test['category']
        if cat not in categories:
            categories[cat] = len(categories)
    
    print(f"\n📂 Найдено категорий: {len(categories)}")
    
    # Создаем Topics для каждой категории
    topics_map = {}
    for category, order in categories.items():
        topic, created = Topic.objects.get_or_create(
            subject=subject,
            title=category,
            defaults={
                'order': order,
                'is_locked': False
            }
        )
        topics_map[category] = topic
        if created:
            print(f"  ✅ Создан Topic: {category}")
    
    # 3. Импортируем тесты как Tasks
    print(f"\n📝 Импорт тестов...")
    
    imported_count = 0
    skipped_count = 0
    missing_answers = []
    
    for test in tests:
        test_id = str(test['id'])
        
        # Проверяем наличие ответа
        if test_id not in answers:
            missing_answers.append(test_id)
            correct_answer = None
        else:
            correct_answer = answers[test_id]
        
        # Пропускаем тесты без ответов
        if not correct_answer:
            skipped_count += 1
            continue
        
        # Получаем Topic для категории
        topic = topics_map.get(test['category'])
        
        # Формируем options как JSON
        options_json = {
            'A': test['options'].get('A', ''),
            'B': test['options'].get('B', ''),
            'C': test['options'].get('C', ''),
            'D': test['options'].get('D', ''),
        }
        
        # Добавляем matching опции если есть
        if test.get('matching_options'):
            options_json['matching'] = {
                'left': {
                    '1': test['matching_options'].get('1', ''),
                    '2': test['matching_options'].get('2', ''),
                    '3': test['matching_options'].get('3', ''),
                    '4': test['matching_options'].get('4', ''),
                },
                'right': {
                    'A': test['matching_options'].get('A', ''),
                    'B': test['matching_options'].get('B', ''),
                    'C': test['matching_options'].get('C', ''),
                    'D': test['matching_options'].get('D', ''),
                }
            }
        
        # Определяем сложность на основе категории
        if 'НАМУНАИ' in test['category']:
            difficulty = 3  # Сложный (пример теста)
        elif 'ИМЛО' in test['category']:
            difficulty = 2  # Средний
        else:
            difficulty = 1  # Легкий
        
        # Создаем или обновляем Task
        task, created = Task.objects.update_or_create(
            id=test['id'],
            defaults={
                'subject': subject,
                'topic': topic,
                'question': test['question_text'],
                'options': options_json,
                'correct_answer': correct_answer,
                'difficulty': difficulty,
                'order': test['id']
            }
        )
        
        imported_count += 1
        
        if imported_count % 100 == 0:
            print(f"  📊 Импортировано: {imported_count}")
    
    # Статистика
    print(f"\n✅ Импорт завершен!")
    print(f"📊 Статистика:")
    print(f"   ✅ Импортировано тестов: {imported_count}")
    print(f"   ⏭️  Пропущено (без ответов): {skipped_count}")
    print(f"   📚 Создано Topics: {len(topics_map)}")
    
    if missing_answers:
        print(f"\n⚠️  Тесты без ответов ({len(missing_answers)}):")
        print(f"   ID: {', '.join(missing_answers[:20])}")
        if len(missing_answers) > 20:
            print(f"   ... и еще {len(missing_answers) - 20}")
    
    # Проверка в БД
    print(f"\n🔍 Проверка в БД:")
    print(f"   Subjects: {Subject.objects.count()}")
    print(f"   Topics: {Topic.objects.count()}")
    print(f"   Tasks: {Task.objects.count()}")
    
    # Примеры
    print(f"\n📝 Примеры импортированных тестов:")
    for task in Task.objects.all()[:3]:
        print(f"\n   ID: {task.id}")
        print(f"   Topic: {task.topic.title if task.topic else 'N/A'}")
        print(f"   Вопрос: {task.question[:60]}...")
        print(f"   Варианты: A, B, C, D")
        print(f"   Правильный ответ: {task.correct_answer}")
        print(f"   Сложность: {task.difficulty}")


if __name__ == "__main__":
    try:
        import_tests()
        print("\n🎉 Импорт успешно завершен!")
    except Exception as e:
        print(f"\n❌ Ошибка при импорте: {e}")
        import traceback
        traceback.print_exc()
