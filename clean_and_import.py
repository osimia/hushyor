#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для очистки старых данных и импорта новых правильных тестов
1. Удаляет все Topics и Tasks для Subject "Забони тоҷикӣ"
2. Импортирует новые правильные данные из test_database_fixed.json
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


def clean_old_data():
    """
    Удаляет старые Topics и Tasks для Subject "Забони тоҷикӣ"
    """
    print("🧹 Очистка старых данных...")
    
    try:
        # Получаем Subject
        subject = Subject.objects.get(title="Забони тоҷикӣ")
        print(f"✅ Найден Subject: {subject.title}")
        
        # Считаем что будет удалено
        old_topics_count = Topic.objects.filter(subject=subject).count()
        old_tasks_count = Task.objects.filter(subject=subject).count()
        
        print(f"\n📊 Будет удалено:")
        print(f"   Topics: {old_topics_count}")
        print(f"   Tasks: {old_tasks_count}")
        
        # Подтверждение
        print(f"\n⚠️  ВНИМАНИЕ! Это удалит все старые данные!")
        confirm = input("Продолжить? (yes/no): ")
        
        if confirm.lower() != 'yes':
            print("❌ Отменено пользователем")
            return False
        
        # Удаляем Tasks
        print(f"\n🗑️  Удаление Tasks...")
        deleted_tasks = Task.objects.filter(subject=subject).delete()
        print(f"   ✅ Удалено Tasks: {deleted_tasks[0]}")
        
        # Удаляем Topics
        print(f"🗑️  Удаление Topics...")
        deleted_topics = Topic.objects.filter(subject=subject).delete()
        print(f"   ✅ Удалено Topics: {deleted_topics[0]}")
        
        print(f"\n✅ Очистка завершена!")
        return True
        
    except Subject.DoesNotExist:
        print("⚠️  Subject 'Забони тоҷикӣ' не найден. Будет создан новый.")
        return True


def import_new_data():
    """
    Импортирует новые правильные данные
    """
    # Пути к файлам
    tests_file = "test_database_fixed.json"
    answers_file = "answer_keys.json"
    
    print("\n📖 Читаю файлы...")
    
    # Проверяем наличие файлов
    if not os.path.exists(tests_file):
        print(f"❌ Файл не найден: {tests_file}")
        return False
    
    if not os.path.exists(answers_file):
        print(f"❌ Файл не найден: {answers_file}")
        return False
    
    # Читаем тесты
    with open(tests_file, 'r', encoding='utf-8') as f:
        tests = json.load(f)
    
    # Читаем ответы
    with open(answers_file, 'r', encoding='utf-8') as f:
        answers = json.load(f)
    
    print(f"📊 Загружено тестов: {len(tests)}")
    print(f"📊 Загружено ответов: {len(answers)}")
    
    # 1. Получаем существующий Subject "Забони тоҷикӣ" (не создаем новый!)
    try:
        subject = Subject.objects.get(title="Забони тоҷикӣ")
        print(f"\n✅ Используем существующий Subject: {subject.title} (ID: {subject.id})")
    except Subject.DoesNotExist:
        # Если не существует, создаем
        subject = Subject.objects.create(
            title="Забони тоҷикӣ",
            icon='📚',
            color='#4CAF50'
        )
        print(f"\n✅ Создан новый Subject: {subject.title} (ID: {subject.id})")
    
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
        status = "✅ Создан" if created else "📌 Существует"
        print(f"   {status}: {category}")
    
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
        difficulty_map = {
            'ФОНЕТИКА ва ҲОДИСАҲОИ ФОНЕТИКӢ': 1,
            'ИМЛО': 1,
            'ЛЕКСИКА': 1,
            'ФРАЗЕОЛОГИЯ': 2,
            'МОРФОЛОГИЯ': 2,
            'СИНТАКСИС': 3,
            'АДАБИЁТ': 3
        }
        difficulty = difficulty_map.get(test['category'], 1)
        
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
            print(f"   📊 Импортировано: {imported_count}")
    
    # Статистика
    print(f"\n✅ Импорт завершен!")
    print(f"\n📊 Итоговая статистика:")
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
    print(f"   Topics: {Topic.objects.filter(subject=subject).count()}")
    print(f"   Tasks: {Task.objects.filter(subject=subject).count()}")
    
    # Распределение по категориям
    print(f"\n📊 Распределение по категориям:")
    for topic in Topic.objects.filter(subject=subject).order_by('order'):
        count = Task.objects.filter(topic=topic).count()
        print(f"   {topic.title}: {count}")
    
    return True


def main():
    """
    Главная функция
    """
    print("=" * 70)
    print("🔄 ОЧИСТКА И ИМПОРТ ДАННЫХ")
    print("=" * 70)
    
    # Шаг 1: Очистка старых данных
    if not clean_old_data():
        print("\n❌ Очистка отменена")
        return
    
    # Шаг 2: Импорт новых данных
    print("\n" + "=" * 70)
    print("📥 ИМПОРТ НОВЫХ ДАННЫХ")
    print("=" * 70)
    
    if import_new_data():
        print("\n" + "=" * 70)
        print("🎉 ВСЕ ГОТОВО!")
        print("=" * 70)
        print("\n✅ Старые данные удалены")
        print("✅ Новые правильные данные импортированы")
        print("✅ Категории соответствуют структуре PDF")
    else:
        print("\n❌ Ошибка при импорте")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
