"""
Django management command для исправления формул в БД
Оборачивает LaTeX формулы в разделители $$
"""

from django.core.management.base import BaseCommand
from core.models import Task
import re


class Command(BaseCommand):
    help = 'Исправляет математические формулы в БД, оборачивая их в $$'

    def handle(self, *args, **options):
        self.stdout.write('🔧 Исправление математических формул в БД...')
        self.stdout.write('=' * 70)
        
        # Получаем все тесты по математике (subject_id=2)
        math_tasks = Task.objects.filter(subject_id=2)
        total_tasks = math_tasks.count()
        
        self.stdout.write(f'\n📊 Найдено тестов по математике: {total_tasks}')
        
        fixed_count = 0
        skipped_count = 0
        
        for idx, task in enumerate(math_tasks, 1):
            # Показываем прогресс каждые 50 тестов
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
            
            # Проверяем, есть ли в вопросе формулы без разделителей $$
            question = task.question
            
            # Паттерн для поиска LaTeX формул без $$
            # Ищем \sqrt, \frac и другие LaTeX команды
            has_latex = bool(re.search(r'\\(sqrt|frac|cdot|times|div|pm|leq|geq|neq|sum|int|lim|begin|end)', question))
            
            # Проверяем, уже обернуты ли формулы в $$
            already_wrapped = '$$' in question
            
            if has_latex and not already_wrapped:
                # Нужно обернуть формулы в $$
                # Простая эвристика: если есть LaTeX команды, оборачиваем весь блок
                
                # Разбиваем текст на части: текст и формулы
                parts = []
                current_pos = 0
                
                # Ищем все LaTeX команды
                for match in re.finditer(r'(\\[a-z]+\{[^}]*\}|\\[a-z]+)', question):
                    start = match.start()
                    
                    # Добавляем текст до формулы
                    if start > current_pos:
                        parts.append(question[current_pos:start])
                    
                    # Находим конец формулы (ищем до конца строки или до следующего текста)
                    formula_start = start
                    formula_end = start
                    
                    # Расширяем формулу, включая все LaTeX команды подряд
                    remaining = question[start:]
                    formula_match = re.match(r'([\\{}\[\]()^_\d\.,\s\+\-\*/=a-zA-Z]+)', remaining)
                    
                    if formula_match:
                        formula_end = start + len(formula_match.group(1))
                        formula = question[formula_start:formula_end].strip()
                        
                        # Оборачиваем в $$
                        parts.append(f' $${formula}$$')
                        current_pos = formula_end
                
                # Добавляем оставшийся текст
                if current_pos < len(question):
                    parts.append(question[current_pos:])
                
                new_question = ''.join(parts)
                
                # Обновляем задание
                task.question = new_question
                task.save(update_fields=['question'])
                fixed_count += 1
            else:
                skipped_count += 1
            
            # Также проверяем варианты ответов
            if task.options:
                options_updated = False
                new_options = {}
                
                for key, value in task.options.items():
                    has_latex_option = bool(re.search(r'\\(sqrt|frac|cdot|times|div|pm|leq|geq|neq|sum|int|lim)', value))
                    already_wrapped_option = '$$' in value
                    
                    if has_latex_option and not already_wrapped_option:
                        # Оборачиваем формулу в $$
                        # Простая эвристика: если вся опция - формула, оборачиваем всю
                        if value.strip().startswith('\\') or '$' in value:
                            new_options[key] = f'$${value.strip()}$$'
                        else:
                            # Ищем формулу внутри текста
                            new_value = re.sub(
                                r'(\\[a-z]+\{[^}]*\}(?:\s*[\\{}\[\]()^_\d\.,\s\+\-\*/=a-zA-Z]*)*)',
                                r'$$\1$$',
                                value
                            )
                            new_options[key] = new_value
                        options_updated = True
                    else:
                        new_options[key] = value
                
                if options_updated:
                    task.options = new_options
                    task.save(update_fields=['options'])
        
        # Переход на новую строку после прогресс-бара
        self.stdout.write('')
        
        # Итоговая статистика
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.SUCCESS('✅ ИСПРАВЛЕНИЕ ЗАВЕРШЕНО!'))
        self.stdout.write('=' * 70)
        self.stdout.write(f'\n📊 Статистика:')
        self.stdout.write(f'  ✅ Исправлено тестов: {fixed_count}')
        self.stdout.write(f'  ⏭️  Пропущено (уже исправлены): {skipped_count}')
        self.stdout.write(f'  📝 Всего обработано: {total_tasks}')
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write('\n💡 Обновите страницу в браузере (Ctrl+Shift+R)')
