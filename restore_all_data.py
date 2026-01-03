#!/usr/bin/env python3
"""
Скрипт восстановления всех данных: таджикский язык + география
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


def clear_existing_data():
    """Очистка существующих данных"""
    print("🗑️  Очистка существующих данных...")
    
    # Удаляем только таджикский язык и географию
    subjects_to_delete = Subject.objects.filter(title__in=['Забони тоҷикӣ', 'География'])
    
    for subject in subjects_to_delete:
        print(f"   Удаление: {subject.title}")
        Task.objects.filter(subject=subject).delete()
        Topic.objects.filter(subject=subject).delete()
        subject.delete()
    
    print("   ✓ Очистка завершена\n")


def import_fixture(fixture_file: str, subject_name: str):
    """Импорт одного fixture файла"""
    
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
    
    # Импорт предметов
    print(f"📚 Импорт предмета {subject_name}...")
    for item in tqdm(subjects_data, desc="Предметы", unit="шт"):
        Subject.objects.update_or_create(
            pk=item['pk'],
            defaults=item['fields']
        )
    
    # Импорт тем
    print(f"\n📖 Импорт тем...")
    for item in tqdm(topics_data, desc="Темы", unit="шт"):
        fields = item['fields'].copy()
        # Преобразуем subject_id в объект Subject
        subject_id = fields.pop('subject')
        fields['subject'] = Subject.objects.get(pk=subject_id)
        
        Topic.objects.update_or_create(
            pk=item['pk'],
            defaults=fields
        )
    
    # Импорт задач
    print(f"\n📝 Импорт задач...")
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
    
    print()


def main():
    print("="*60)
    print("🔄 ВОССТАНОВЛЕНИЕ ДАННЫХ")
    print("="*60)
    print()
    
    start_time = time.time()
    
    with transaction.atomic():
        # Очистка
        clear_existing_data()
        
        # Импорт таджикского языка
        print("="*60)
        print("1️⃣  ТАДЖИКСКИЙ ЯЗЫК")
        print("="*60)
        print()
        import_fixture('tjk_data.json', 'Забони тоҷикӣ')
        
        # Импорт географии
        print("="*60)
        print("2️⃣  ГЕОГРАФИЯ")
        print("="*60)
        print()
        import_fixture('geography_data.json', 'География')
    
    elapsed_time = time.time() - start_time
    
    # Итоговая статистика
    print("="*60)
    print("✅ ВОССТАНОВЛЕНИЕ ЗАВЕРШЕНО!")
    print("="*60)
    print(f"⏱️  Время выполнения: {elapsed_time:.2f} секунд")
    print()
    
    # Проверка
    print("📊 Итоговая статистика:")
    print()
    
    for subject_title in ['Забони тоҷикӣ', 'География']:
        subject = Subject.objects.filter(title=subject_title).first()
        if subject:
            topics_count = Topic.objects.filter(subject=subject).count()
            tasks_count = Task.objects.filter(subject=subject).count()
            
            print(f"   {subject.icon} {subject.title}")
            print(f"      Тем: {topics_count}")
            print(f"      Задач: {tasks_count}")
            
            # Топ-3 темы по количеству задач
            top_topics = Topic.objects.filter(subject=subject).order_by('order')[:3]
            for topic in top_topics:
                topic_tasks = Task.objects.filter(topic=topic).count()
                print(f"         • {topic.title}: {topic_tasks} задач")
            print()
    
    print("🎉 Все данные успешно восстановлены!")


if __name__ == '__main__':
    try:
        main()
    except FileNotFoundError as e:
        print(f"❌ Ошибка: файл не найден - {e}")
        print("   Убедитесь что файлы tjk_data.json и geography_data.json существуют")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Ошибка при восстановлении: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
