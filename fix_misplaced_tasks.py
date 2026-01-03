#!/usr/bin/env python3
"""
Скрипт для автоматического исправления задач таджикского языка в географии
Находит и переносит их в правильный предмет
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


def fix_misplaced_tasks():
    """Автоматически исправляет задачи таджикского языка в географии"""
    
    print("="*60)
    print("🔧 АВТОМАТИЧЕСКОЕ ИСПРАВЛЕНИЕ ЗАДАЧ")
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
        'нутқ', 'гап', 'сухан', 'баёни', 'ифода',
        'адабий', 'забонӣ', 'тоҷикӣ', 'форсӣ'
    ]
    
    # Ищем задачи для перемещения
    tasks_to_move = []
    
    print("🔍 Поиск задач таджикского языка в географии...")
    print()
    
    for task in geography_tasks:
        question_lower = task.question.lower()
        
        # Проверяем наличие ключевых слов
        for keyword in tajik_keywords:
            if keyword in question_lower:
                tasks_to_move.append(task)
                break
    
    if not tasks_to_move:
        print("✅ Подозрительных задач не найдено!")
        print("   Все задачи в географии выглядят корректно.")
        return
    
    print(f"⚠️  Найдено {len(tasks_to_move)} задач для перемещения:")
    print()
    
    # Показываем первые 10 задач
    for i, task in enumerate(tasks_to_move[:10], 1):
        print(f"{i}. ID: {task.id}")
        print(f"   Вопрос: {task.question[:80]}...")
        if task.topic:
            print(f"   Тема: {task.topic.title}")
        print()
    
    if len(tasks_to_move) > 10:
        print(f"   ... и еще {len(tasks_to_move) - 10} задач")
        print()
    
    # Запрашиваем подтверждение
    print("="*60)
    response = input(f"Переместить {len(tasks_to_move)} задач в 'Забони тоҷикӣ'? (yes/no): ").strip().lower()
    
    if response not in ['yes', 'y', 'да', 'д']:
        print("\n❌ Отменено пользователем")
        return
    
    print()
    print("🔄 Перемещение задач...")
    
    # Перемещаем задачи
    with transaction.atomic():
        moved_count = 0
        
        for task in tasks_to_move:
            old_subject = task.subject.title
            task.subject = tajik
            task.save()
            moved_count += 1
            
            if moved_count % 50 == 0:
                print(f"   Перемещено: {moved_count}/{len(tasks_to_move)}")
    
    print()
    print("="*60)
    print("✅ ИСПРАВЛЕНИЕ ЗАВЕРШЕНО!")
    print("="*60)
    print(f"Перемещено задач: {moved_count}")
    print()
    
    # Итоговая статистика
    print("📊 Итоговая статистика:")
    print()
    
    geography_count = Task.objects.filter(subject=geography).count()
    tajik_count = Task.objects.filter(subject=tajik).count()
    
    print(f"   🌍 География: {geography_count} задач")
    print(f"   📚 Забони тоҷикӣ: {tajik_count} задач")
    print()
    
    # Проверяем остались ли подозрительные задачи
    remaining_geography = Task.objects.filter(subject=geography)
    suspicious_remaining = []
    
    for task in remaining_geography:
        question_lower = task.question.lower()
        for keyword in tajik_keywords:
            if keyword in question_lower:
                suspicious_remaining.append(task)
                break
    
    if suspicious_remaining:
        print(f"⚠️  Внимание: осталось {len(suspicious_remaining)} подозрительных задач в географии")
        print("   Возможно, они содержат общие слова. Проверьте вручную:")
        for task in suspicious_remaining[:5]:
            print(f"   - ID {task.id}: {task.question[:60]}...")
    else:
        print("✅ Все задачи таджикского языка успешно перемещены!")
    
    print()
    print("🎉 Готово!")


if __name__ == '__main__':
    try:
        fix_misplaced_tasks()
    except KeyboardInterrupt:
        print("\n\n❌ Прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
