#!/usr/bin/env python3
"""
Скрипт для автоматического исправления тем и задач таджикского языка в географии
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


def fix_topics_and_tasks():
    """Автоматически исправляет темы и задачи таджикского языка в географии"""
    
    print("="*60)
    print("🔧 АВТОМАТИЧЕСКОЕ ИСПРАВЛЕНИЕ ТЕМ И ЗАДАЧ")
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
    
    # Ключевые слова таджикского языка для тем
    tajik_topic_keywords = [
        'забон', 'адабиёт', 'грамматика', 'имло', 'луғат',
        'нутқ', 'тоҷикӣ', 'форсӣ', 'адабий', 'забонӣ',
        'калима', 'ҷумла', 'матн', 'шеър'
    ]
    
    # Ключевые слова для задач
    tajik_task_keywords = [
        'забон', 'калима', 'ҷумла', 'матн', 'шеър', 'адабиёт',
        'нависанда', 'шоир', 'асар', 'достон', 'ҳикоя',
        'грамматика', 'имло', 'луғат', 'маъно', 'тарҷума',
        'феъл', 'исм', 'сифат', 'ҳарф', 'овоз', 'садо',
        'нутқ', 'гап', 'сухан', 'баёни', 'ифода',
        'адабий', 'забонӣ', 'тоҷикӣ', 'форсӣ'
    ]
    
    # ШАГ 1: Проверяем темы
    print("="*60)
    print("ШАГ 1: ПРОВЕРКА ТЕМ")
    print("="*60)
    print()
    
    geography_topics = Topic.objects.filter(subject=geography)
    print(f"Всего тем в географии: {geography_topics.count()}")
    print()
    
    topics_to_move = []
    
    print("🔍 Поиск тем таджикского языка в географии...")
    print()
    
    for topic in geography_topics:
        title_lower = topic.title.lower()
        
        # Проверяем наличие ключевых слов в названии темы
        for keyword in tajik_topic_keywords:
            if keyword in title_lower:
                topics_to_move.append(topic)
                print(f"   ✓ Найдена тема: ID={topic.id} - {topic.title}")
                break
    
    print()
    
    if topics_to_move:
        print(f"⚠️  Найдено {len(topics_to_move)} тем для перемещения")
    else:
        print("✅ Подозрительных тем не найдено")
    
    print()
    
    # ШАГ 2: Проверяем задачи
    print("="*60)
    print("ШАГ 2: ПРОВЕРКА ЗАДАЧ")
    print("="*60)
    print()
    
    geography_tasks = Task.objects.filter(subject=geography).select_related('topic')
    print(f"Всего задач в географии: {geography_tasks.count()}")
    print()
    
    tasks_to_move = []
    
    print("🔍 Поиск задач таджикского языка в географии...")
    print()
    
    for task in geography_tasks:
        question_lower = task.question.lower()
        
        # Проверяем наличие ключевых слов
        for keyword in tajik_task_keywords:
            if keyword in question_lower:
                tasks_to_move.append(task)
                break
    
    if tasks_to_move:
        print(f"⚠️  Найдено {len(tasks_to_move)} задач для перемещения")
        print()
        print("Примеры найденных задач:")
        for i, task in enumerate(tasks_to_move[:5], 1):
            print(f"   {i}. ID: {task.id}")
            print(f"      Вопрос: {task.question[:70]}...")
            if task.topic:
                print(f"      Тема: {task.topic.title}")
            print()
    else:
        print("✅ Подозрительных задач не найдено")
    
    print()
    
    # Если ничего не найдено
    if not topics_to_move and not tasks_to_move:
        print("="*60)
        print("✅ ВСЁ В ПОРЯДКЕ!")
        print("="*60)
        print("Все темы и задачи в географии выглядят корректно.")
        return
    
    # Запрашиваем подтверждение
    print("="*60)
    print("ИТОГО К ПЕРЕМЕЩЕНИЮ:")
    print(f"   Тем: {len(topics_to_move)}")
    print(f"   Задач: {len(tasks_to_move)}")
    print("="*60)
    print()
    
    response = input("Переместить в 'Забони тоҷикӣ'? (yes/no): ").strip().lower()
    
    if response not in ['yes', 'y', 'да', 'д']:
        print("\n❌ Отменено пользователем")
        return
    
    print()
    print("🔄 Перемещение...")
    print()
    
    # Перемещаем
    with transaction.atomic():
        # Сначала темы
        if topics_to_move:
            print(f"📖 Перемещение {len(topics_to_move)} тем...")
            for topic in topics_to_move:
                topic.subject = tajik
                topic.save()
                print(f"   ✓ Тема ID={topic.id}: {topic.title}")
            print()
        
        # Потом задачи
        if tasks_to_move:
            print(f"📝 Перемещение {len(tasks_to_move)} задач...")
            moved_count = 0
            
            for task in tasks_to_move:
                task.subject = tajik
                task.save()
                moved_count += 1
                
                if moved_count % 50 == 0:
                    print(f"   Перемещено: {moved_count}/{len(tasks_to_move)}")
            
            print(f"   ✓ Перемещено: {moved_count}/{len(tasks_to_move)}")
            print()
    
    print("="*60)
    print("✅ ИСПРАВЛЕНИЕ ЗАВЕРШЕНО!")
    print("="*60)
    print()
    
    # Итоговая статистика
    print("📊 Итоговая статистика:")
    print()
    
    geography_topics_count = Topic.objects.filter(subject=geography).count()
    geography_tasks_count = Task.objects.filter(subject=geography).count()
    tajik_topics_count = Topic.objects.filter(subject=tajik).count()
    tajik_tasks_count = Task.objects.filter(subject=tajik).count()
    
    print(f"   🌍 География:")
    print(f"      Тем: {geography_topics_count}")
    print(f"      Задач: {geography_tasks_count}")
    print()
    print(f"   📚 Забони тоҷикӣ:")
    print(f"      Тем: {tajik_topics_count}")
    print(f"      Задач: {tajik_tasks_count}")
    print()
    
    print("🎉 Готово!")


if __name__ == '__main__':
    try:
        fix_topics_and_tasks()
    except KeyboardInterrupt:
        print("\n\n❌ Прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
