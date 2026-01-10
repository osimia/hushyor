#!/usr/bin/env python3
"""
Скрипт для проверки занятых ID в базе данных
"""

import os
import sys
import django

# Настройка Django окружения
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from core.models import Subject, Topic, Task

def check_database_ids():
    """Проверка текущих ID в базе данных"""
    
    print("="*70)
    print("ПРОВЕРКА ЗАНЯТЫХ ID В БАЗЕ ДАННЫХ")
    print("="*70)
    print()
    
    # Проверяем Subject
    subjects = Subject.objects.all().order_by('id')
    print(f"📚 ПРЕДМЕТЫ (Subject):")
    print(f"   Всего: {subjects.count()}")
    if subjects.exists():
        print(f"   Занятые ID: {list(subjects.values_list('id', flat=True))}")
        max_subject_id = subjects.last().id
        print(f"   Максимальный ID: {max_subject_id}")
        print(f"   ✅ Следующий свободный ID: {max_subject_id + 1}")
    else:
        print(f"   ✅ Следующий свободный ID: 1")
    print()
    
    # Проверяем Topic
    topics = Topic.objects.all().order_by('id')
    print(f"📁 ТОПИКИ (Topic):")
    print(f"   Всего: {topics.count()}")
    if topics.exists():
        topic_ids = list(topics.values_list('id', flat=True))
        print(f"   Занятые ID: {topic_ids[:20]}{'...' if len(topic_ids) > 20 else ''}")
        max_topic_id = topics.last().id
        print(f"   Максимальный ID: {max_topic_id}")
        print(f"   ✅ Следующий свободный ID: {max_topic_id + 1}")
    else:
        print(f"   ✅ Следующий свободный ID: 1")
    print()
    
    # Проверяем Task
    tasks = Task.objects.all().order_by('id')
    print(f"📝 ТЕСТЫ (Task):")
    print(f"   Всего: {tasks.count()}")
    if tasks.exists():
        task_ids = list(tasks.values_list('id', flat=True))
        print(f"   Занятые ID: {task_ids[:20]}{'...' if len(task_ids) > 20 else ''}")
        max_task_id = tasks.last().id
        print(f"   Максимальный ID: {max_task_id}")
        print(f"   ✅ Следующий свободный ID: {max_task_id + 1}")
    else:
        print(f"   ✅ Следующий свободный ID: 1")
    print()
    
    # Детальная информация по предметам
    print("="*70)
    print("ДЕТАЛЬНАЯ ИНФОРМАЦИЯ ПО ПРЕДМЕТАМ:")
    print("="*70)
    for subject in subjects:
        topics_count = subject.topics.count()
        tasks_count = subject.tasks.count()
        print(f"\n📚 {subject.title} (ID: {subject.id})")
        print(f"   Топиков: {topics_count}")
        print(f"   Тестов: {tasks_count}")
        
        if topics_count > 0:
            print(f"   Топики:")
            for topic in subject.topics.all().order_by('order'):
                topic_tasks = topic.tasks.count()
                print(f"      - {topic.title} (ID: {topic.id}): {topic_tasks} тестов")
    
    print()
    print("="*70)
    print("ВЫВОД:")
    print("="*70)
    print("При импорте новых данных Django автоматически использует")
    print("следующие свободные ID, поэтому конфликтов не будет.")
    print("="*70)

if __name__ == '__main__':
    check_database_ids()
