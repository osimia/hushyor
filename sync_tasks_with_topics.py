#!/usr/bin/env python3
"""
Скрипт для синхронизации предмета задач с предметом их тем
Если тема принадлежит "Забони тоҷикӣ", то и все её задачи должны быть в этом предмете
"""

import os
import sys
import django
from pathlib import Path

# Настройка Django
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.db import transaction
from core.models import Subject, Topic, Task


def sync_tasks_with_topics():
    """Синхронизирует предмет задач с предметом их тем"""
    
    print("="*60)
    print("🔄 СИНХРОНИЗАЦИЯ ЗАДАЧ С ТЕМАМИ")
    print("="*60)
    print()
    
    # Получаем предметы
    geography = Subject.objects.filter(title="География").first()
    tajik = Subject.objects.filter(title="Забони тоҷикӣ").first()
    
    if not geography:
        print("❌ Предмет 'География' не найден в БД")
        return
    
    if not tajik:
        print("❌ Предмет 'Забони тоҷикӣ' не найден в БД")
        return
    
    print(f"📚 География (ID={geography.id})")
    print(f"📚 Забони тоҷикӣ (ID={tajik.id})")
    print()
    
    # Получаем все темы таджикского языка
    tajik_topics = Topic.objects.filter(subject=tajik)
    
    print(f"Тем в 'Забони тоҷикӣ': {tajik_topics.count()}")
    print()
    
    if tajik_topics.count() == 0:
        print("⚠️  Нет тем в 'Забони тоҷикӣ'")
        return
    
    print("📖 Темы таджикского языка:")
    for topic in tajik_topics:
        task_count = Task.objects.filter(topic=topic).count()
        print(f"   - {topic.title} (ID={topic.id}): {task_count} задач")
    print()
    
    # Находим задачи, которые принадлежат темам таджикского языка,
    # но имеют неправильный предмет
    print("🔍 Поиск задач с неправильным предметом...")
    print()
    
    tasks_to_fix = []
    
    for topic in tajik_topics:
        # Находим все задачи этой темы
        topic_tasks = Task.objects.filter(topic=topic)
        
        for task in topic_tasks:
            # Если предмет задачи не совпадает с предметом темы
            if task.subject.id != topic.subject.id:
                tasks_to_fix.append({
                    'task': task,
                    'topic': topic,
                    'current_subject': task.subject.title,
                    'correct_subject': topic.subject.title
                })
    
    if not tasks_to_fix:
        print("✅ Все задачи уже синхронизированы с темами!")
        print("   Ничего исправлять не нужно.")
        return
    
    print(f"⚠️  Найдено {len(tasks_to_fix)} задач с неправильным предметом:")
    print()
    
    # Показываем примеры
    for i, item in enumerate(tasks_to_fix[:10], 1):
        task = item['task']
        topic = item['topic']
        print(f"{i}. ID: {task.id}")
        print(f"   Тема: {topic.title}")
        print(f"   Текущий предмет: {item['current_subject']}")
        print(f"   Должен быть: {item['correct_subject']}")
        print(f"   Вопрос: {task.question[:60]}...")
        print()
    
    if len(tasks_to_fix) > 10:
        print(f"   ... и еще {len(tasks_to_fix) - 10} задач")
        print()
    
    # Группируем по предметам
    by_subject = {}
    for item in tasks_to_fix:
        current = item['current_subject']
        if current not in by_subject:
            by_subject[current] = 0
        by_subject[current] += 1
    
    print("📊 Распределение по текущим предметам:")
    for subject_name, count in by_subject.items():
        print(f"   {subject_name}: {count} задач")
    print()
    
    # Запрашиваем подтверждение
    print("="*60)
    response = input(f"Исправить предмет у {len(tasks_to_fix)} задач? (yes/no): ").strip().lower()
    
    if response not in ['yes', 'y', 'да', 'д']:
        print("\n❌ Отменено пользователем")
        return
    
    print()
    print("🔄 Синхронизация...")
    print()
    
    # Исправляем задачи
    with transaction.atomic():
        fixed_count = 0
        
        for item in tasks_to_fix:
            task = item['task']
            topic = item['topic']
            
            # Устанавливаем предмет задачи равным предмету темы
            task.subject = topic.subject
            task.save()
            
            fixed_count += 1
            
            if fixed_count % 50 == 0:
                print(f"   Исправлено: {fixed_count}/{len(tasks_to_fix)}")
        
        print(f"   ✓ Исправлено: {fixed_count}/{len(tasks_to_fix)}")
    
    print()
    print("="*60)
    print("✅ СИНХРОНИЗАЦИЯ ЗАВЕРШЕНА!")
    print("="*60)
    print()
    
    # Итоговая статистика
    print("📊 Итоговая статистика:")
    print()
    
    for topic in tajik_topics:
        task_count = Task.objects.filter(topic=topic).count()
        correct_count = Task.objects.filter(topic=topic, subject=tajik).count()
        print(f"   📖 {topic.title}:")
        print(f"      Всего задач: {task_count}")
        print(f"      С правильным предметом: {correct_count}")
        if task_count != correct_count:
            print(f"      ⚠️  Несоответствие: {task_count - correct_count} задач")
        print()
    
    # Общая статистика
    geography_tasks = Task.objects.filter(subject=geography).count()
    tajik_tasks = Task.objects.filter(subject=tajik).count()
    
    print("Общая статистика по предметам:")
    print(f"   🌍 География: {geography_tasks} задач")
    print(f"   📚 Забони тоҷикӣ: {tajik_tasks} задач")
    print()
    
    print("🎉 Готово!")


if __name__ == '__main__':
    try:
        sync_tasks_with_topics()
    except KeyboardInterrupt:
        print("\n\n❌ Прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
