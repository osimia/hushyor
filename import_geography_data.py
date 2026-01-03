#!/usr/bin/env python3
"""
Скрипт импорта данных по географии с отображением прогресса
"""

import os
import sys
import json
import django
from pathlib import Path

# Настройка Django
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.db import transaction
from core.models import Subject, Topic, Task
from tqdm import tqdm
import time


def import_geography_data(fixture_file: str = "geography_data.json"):
    """Импорт данных по географии с прогресс-баром"""
    
    print("🌍 Импорт данных по географии...")
    print()
    
    # Загружаем fixture
    print(f"📂 Загрузка {fixture_file}...")
    with open(fixture_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Разделяем по типам
    subjects_data = [item for item in data if item['model'] == 'core.subject']
    topics_data = [item for item in data if item['model'] == 'core.topic']
    tasks_data = [item for item in data if item['model'] == 'core.task']
    
    print(f"   Предметов: {len(subjects_data)}")
    print(f"   Тем: {len(topics_data)}")
    print(f"   Задач: {len(tasks_data)}")
    print()
    
    start_time = time.time()
    
    with transaction.atomic():
        # 1. Импорт предметов
        print("📚 Импорт предметов...")
        for item in tqdm(subjects_data, desc="Предметы", unit="шт"):
            Subject.objects.update_or_create(
                pk=item['pk'],
                defaults=item['fields']
            )
        
        # 2. Импорт тем
        print("\n📖 Импорт тем...")
        for item in tqdm(topics_data, desc="Темы", unit="шт"):
            fields = item['fields'].copy()
            # Преобразуем subject_id в объект Subject
            subject_id = fields.pop('subject')
            fields['subject'] = Subject.objects.get(pk=subject_id)
            
            Topic.objects.update_or_create(
                pk=item['pk'],
                defaults=fields
            )
        
        # 3. Импорт задач
        print("\n📝 Импорт задач...")
        for item in tqdm(tasks_data, desc="Задачи", unit="шт"):
            fields = item['fields'].copy()
            # Преобразуем subject_id и topic_id в объекты
            subject_id = fields.pop('subject')
            fields['subject'] = Subject.objects.get(pk=subject_id)
            
            topic_id = fields.pop('topic', None)
            if topic_id:
                fields['topic'] = Topic.objects.get(pk=topic_id)
            
            Task.objects.update_or_create(
                pk=item['pk'],
                defaults=fields
            )
    
    elapsed_time = time.time() - start_time
    
    # Статистика
    print("\n" + "="*60)
    print("✅ Импорт завершен успешно!")
    print("="*60)
    print(f"⏱️  Время выполнения: {elapsed_time:.2f} секунд")
    print()
    
    # Проверка импорта
    geography_subject = Subject.objects.filter(title="География").first()
    if geography_subject:
        topics_count = Topic.objects.filter(subject=geography_subject).count()
        tasks_count = Task.objects.filter(subject=geography_subject).count()
        
        print("📊 Статистика по географии:")
        print(f"   Предмет: {geography_subject.title} {geography_subject.icon}")
        print(f"   Тем: {topics_count}")
        print(f"   Задач: {tasks_count}")
        print()
        
        # Статистика по темам
        print("📋 Задачи по темам:")
        for topic in Topic.objects.filter(subject=geography_subject).order_by('order'):
            topic_tasks = Task.objects.filter(topic=topic).count()
            print(f"   {topic.title}: {topic_tasks} задач")
    
    print()
    print("🎉 Готово! Данные по географии успешно импортированы в базу данных.")


if __name__ == '__main__':
    try:
        import_geography_data()
    except FileNotFoundError:
        print("❌ Ошибка: файл geography_data.json не найден!")
        print("   Сначала запустите: python3 parse_geography_improved.py")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Ошибка при импорте: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
