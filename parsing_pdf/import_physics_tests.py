#!/usr/bin/env python3
"""
Скрипт для импорта тестов по предмету Физика в базу данных Django
ВАЖНО: Запускать из корневой директории проекта с активированным окружением Django
"""

import os
import sys
import django
import json

# Настройка Django окружения
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from core.models import Subject, Topic, Task

def import_physics_tests(json_file_path):
    """Импорт тестов из JSON файла"""
    
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    subject_title = data['subject']
    topics_data = data['topics']
    
    print(f"Начинаем импорт предмета: {subject_title}")
    
    # Проверяем, существует ли уже предмет
    subject, created = Subject.objects.get_or_create(
        title=subject_title,
        defaults={
            'icon': '⚛️',  # Иконка атома для физики
            'color': '#4169E1'  # Королевский синий цвет
        }
    )
    
    if created:
        print(f"✅ Создан новый предмет: {subject.title} (ID: {subject.id})")
    else:
        print(f"ℹ️  Предмет уже существует: {subject.title} (ID: {subject.id})")
        # Удаляем старые данные если они есть
        old_topics_count = subject.topics.count()
        old_tasks_count = subject.tasks.count()
        if old_topics_count > 0 or old_tasks_count > 0:
            print(f"⚠️  Удаляем старые данные: {old_topics_count} топиков, {old_tasks_count} тестов")
            subject.topics.all().delete()
            subject.tasks.all().delete()
    
    # Импортируем топики и тесты
    total_tasks = 0
    
    for topic_data in topics_data:
        topic = Topic.objects.create(
            subject=subject,
            title=topic_data['title'],
            order=topic_data['order'],
            is_locked=False
        )
        print(f"  📁 Создан топик: {topic.title} (ID: {topic.id})")
        
        # Импортируем тесты для этого топика
        tasks_data = topic_data['tasks']
        tasks_to_create = []
        
        for task_data in tasks_data:
            task = Task(
                subject=subject,
                topic=topic,
                question=task_data['question'],
                options=task_data['options'],
                correct_answer=task_data['correct_answer'],
                difficulty=task_data['difficulty'],
                order=task_data['original_test_id'],
                original_test_id=task_data['original_test_id']
            )
            tasks_to_create.append(task)
        
        # Массовое создание тестов для производительности
        Task.objects.bulk_create(tasks_to_create)
        print(f"    ✅ Импортировано {len(tasks_to_create)} тестов")
        total_tasks += len(tasks_to_create)
    
    print(f"\n{'='*60}")
    print(f"✅ ИМПОРТ ЗАВЕРШЕН УСПЕШНО!")
    print(f"{'='*60}")
    print(f"Предмет: {subject.title} (ID: {subject.id})")
    print(f"Топиков: {len(topics_data)}")
    print(f"Всего тестов: {total_tasks}")
    print(f"{'='*60}\n")
    
    # Выводим информацию о топиках
    print("Детальная статистика по топикам:")
    for topic in subject.topics.all().order_by('order'):
        task_count = topic.tasks.count()
        print(f"  {topic.order}. {topic.title}: {task_count} тестов (ID: {topic.id})")

def main():
    json_file = os.path.join(os.path.dirname(__file__), 'physics_tests_import.json')
    
    if not os.path.exists(json_file):
        print(f"❌ Файл не найден: {json_file}")
        sys.exit(1)
    
    print("="*60)
    print("ИМПОРТ ТЕСТОВ ПО ПРЕДМЕТУ ФИЗИКА")
    print("="*60)
    print()
    
    # Показываем текущее состояние БД
    print("Текущие предметы в базе данных:")
    for subj in Subject.objects.all():
        topics_count = subj.topics.count()
        tasks_count = subj.tasks.count()
        print(f"  - {subj.title} (ID: {subj.id}): {topics_count} топиков, {tasks_count} тестов")
    print()
    
    # Импортируем данные
    import_physics_tests(json_file)

if __name__ == '__main__':
    main()
