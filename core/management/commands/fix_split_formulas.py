"""
Django management command для исправления разбитых формул
Объединяет несколько $$...$$ блоков в один
"""

from django.core.management.base import BaseCommand
from core.models import Task
import re


class Command(BaseCommand):
    help = 'Исправляет разбитые математические формулы, объединяя их в один блок'

    def handle(self, *args, **options):
        self.stdout.write('🔧 Исправление разбитых формул в БД...')
        self.stdout.write('=' * 70)
        
        # Получаем все тесты по математике
        math_tasks = Task.objects.filter(subject_id=2)
        total_tasks = math_tasks.count()
        
        self.stdout.write(f'\n📊 Найдено тестов по математике: {total_tasks}')
        
        fixed_count = 0
        
        for idx, task in enumerate(math_tasks, 1):
            # Показываем прогресс
            if idx % 50 == 0 or idx == total_tasks:
                progress = (idx / total_tasks) * 100
                bar_length = 30
                filled = int(bar_length * idx / total_tasks)
                bar = '█' * filled + '░' * (bar_length - filled)
                self.stdout.write(
                    f'\r📊 [{bar}] {idx}/{total_tasks} ({progress:.0f}%)',
                    ending=''
                )
                self.stdout.flush()
            
            question = task.question
            
            # Проверяем, есть ли несколько блоков $$...$$ подряд
            formula_blocks = re.findall(r'\$\$([^$]+)\$\$', question)
            
            if len(formula_blocks) > 1:
                # Есть несколько формул подряд - объединяем их
                
                # Удаляем все блоки $$...$$
                text_without_formulas = re.sub(r'\$\$[^$]+\$\$', '', question)
                
                # Объединяем все формулы в одну
                combined_formula = ' '.join(formula_blocks)
                
                # Очищаем формулу от лишних символов
                combined_formula = combined_formula.strip()
                
                # Удаляем дубликаты частей формулы
                # Например, если есть \sqrt{2,5} несколько раз, оставляем один
                parts = []
                seen = set()
                for part in combined_formula.split():
                    if part not in seen or part in ['\\cdot', '+', '-', ':', '=']:
                        parts.append(part)
                        seen.add(part)
                
                combined_formula = ' '.join(parts)
                
                # Создаем новый вопрос с одной формулой
                new_question = text_without_formulas.strip() + ' $$' + combined_formula + '$$'
                
                # Обновляем задание
                task.question = new_question
                task.save(update_fields=['question'])
                fixed_count += 1
        
        # Переход на новую строку
        self.stdout.write('')
        
        # Итоговая статистика
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.SUCCESS('✅ ИСПРАВЛЕНИЕ ЗАВЕРШЕНО!'))
        self.stdout.write('=' * 70)
        self.stdout.write(f'\n📊 Статистика:')
        self.stdout.write(f'  ✅ Исправлено тестов: {fixed_count}')
        self.stdout.write(f'  📝 Всего обработано: {total_tasks}')
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write('\n💡 Обновите страницу в браузере (Ctrl+Shift+R)')
