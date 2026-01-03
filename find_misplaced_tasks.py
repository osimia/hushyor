#!/usr/bin/env python3
"""
Скрипт для поиска задач таджикского языка, которые попали в географию
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

from core.models import Subject, Topic, Task


def find_misplaced_tasks():
    """Находит задачи таджикского языка в предмете География"""
    
    print("🔍 Поиск задач таджикского языка в географии...")
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
    
    # Получаем все задачи географии
    geography_tasks = Task.objects.filter(subject=geography).select_related('topic')
    
    print(f"Всего задач в географии: {geography_tasks.count()}")
    print()
    
    # Ключевые слова таджикского языка
    tajik_keywords = [
        'забон', 'калима', 'ҷумла', 'матн', 'шеър', 'адабиёт',
        'нависанда', 'шоир', 'асар', 'достон', 'ҳикоя',
        'грамматика', 'имло', 'луғат', 'маъно', 'тарҷума',
        'феъл', 'исм', 'сифат', 'ҳарф', 'овоз', 'садо',
        'нутқ', 'гап', 'сухан', 'баёни', 'ифода'
    ]
    
    # Ищем подозрительные задачи
    suspicious_tasks = []
    
    for task in geography_tasks:
        question_lower = task.question.lower()
        
        # Проверяем наличие ключевых слов
        for keyword in tajik_keywords:
            if keyword in question_lower:
                suspicious_tasks.append({
                    'task': task,
                    'keyword': keyword
                })
                break
    
    if suspicious_tasks:
        print(f"⚠️  Найдено {len(suspicious_tasks)} подозрительных задач:")
        print()
        
        for item in suspicious_tasks:
            task = item['task']
            keyword = item['keyword']
            
            print(f"ID: {task.id}")
            print(f"Тема: {task.topic.title if task.topic else 'Без темы'}")
            print(f"Вопрос: {task.question[:100]}...")
            print(f"Ключевое слово: '{keyword}'")
            print("-" * 80)
        
        print()
        print("📋 Для исправления:")
        print("1. Зайди в админку: http://localhost:8000/admin/core/task/")
        print(f"2. Отфильтруй по предмету 'География'")
        print(f"3. Найди задачи с ID: {', '.join(str(t['task'].id) for t in suspicious_tasks[:10])}")
        print("4. Выбери их и используй действие 'Изменить предмет для выбранных задач'")
        print("5. Выбери предмет 'Забони тоҷикӣ'")
        print()
        
        # Создаем SQL для быстрого исправления
        task_ids = [str(t['task'].id) for t in suspicious_tasks]
        print("🔧 Или выполни SQL запрос для быстрого исправления:")
        print()
        print(f"UPDATE core_task SET subject_id = {tajik.id} WHERE id IN ({', '.join(task_ids)});")
        print()
        
    else:
        print("✅ Подозрительных задач не найдено!")
        print("   Все задачи в географии выглядят корректно.")
    
    # Дополнительная проверка: задачи без темы
    print()
    print("📊 Дополнительная статистика:")
    
    tasks_without_topic = geography_tasks.filter(topic__isnull=True).count()
    print(f"   Задач без темы: {tasks_without_topic}")
    
    # Статистика по темам
    print()
    print("   Распределение по темам:")
    topics = Topic.objects.filter(subject=geography)
    for topic in topics:
        count = Task.objects.filter(topic=topic).count()
        print(f"      {topic.title}: {count} задач")


if __name__ == '__main__':
    try:
        find_misplaced_tasks()
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
