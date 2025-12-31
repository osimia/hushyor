from django.core.management.base import BaseCommand
import re
import PyPDF2
from core.models import Subject, Topic, Task


class Command(BaseCommand):
    help = 'Импортирует задания из PDF файла в базу данных'

    def add_arguments(self, parser):
        parser.add_argument('pdf_file', type=str, help='Путь к PDF файлу')
        parser.add_argument('--subject', type=str, default='Математика', help='Название предмета')

    def handle(self, *args, **options):
        pdf_path = options['pdf_file']
        subject_name = options['subject']
        
        self.stdout.write(self.style.SUCCESS(f'📖 Чтение PDF файла: {pdf_path}'))
        
        # Извлекаем текст из PDF
        text = self.extract_text_from_pdf(pdf_path)
        
        if not text:
            self.stdout.write(self.style.ERROR('❌ Не удалось извлечь текст из PDF'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'✅ Извлечено {len(text)} символов'))
        
        # Парсим задания
        self.stdout.write('🔍 Парсинг заданий...')
        tasks = self.parse_tasks_from_text(text)
        
        self.stdout.write(self.style.SUCCESS(f'✅ Найдено {len(tasks)} заданий'))
        
        if tasks:
            # Сохраняем в БД
            self.stdout.write('💾 Сохранение в базу данных...')
            self.save_tasks_to_db(tasks, subject_name)
            self.stdout.write(self.style.SUCCESS('✅ Импорт завершен!'))
        else:
            self.stdout.write(self.style.WARNING('⚠️  Задания не найдены'))
            self.stdout.write('Первые 500 символов:')
            self.stdout.write(text[:500])

    def extract_text_from_pdf(self, pdf_path):
        """Извлекает текст из PDF файла"""
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ошибка при чтении PDF: {e}"))
        return text

    def parse_tasks_from_text(self, text):
        """Парсит задания из текста"""
        tasks = []
        current_topic = None
        
        # Список тем, которые нас интересуют
        valid_topics = [
            'ДЕЙСТВИЯ  С РАЦИОНАЛЬНЫМИ И  ИРРАЦИОНАЛЬНЫМИ  ЧИСЛАМИ',
            'КВАДРАТНЫЕ  КОРНИ',
            'АЛГЕБРАИЧЕСКИЕ  УТВЕРЖДЕНИЯ',
            'РАЦИОНАЛЬНЫЕ  И ИРРАЦИОНАЛЬНЫЕ  УРАВНЕНИЯ  И СИСТЕМЫ',
            'ТЕКСТОВЫЕ ЗАДАЧИ',
            'ПРИМЕНЕНИЕ  ФОРМУЛ',
            'ТАБЛИЦЫ  И ДИАГРАММЫ',
            'НЕРАВЕНСТВА  И СИСТЕМЫ  НЕРАВЕНСТВА',
            'ТРИГОНОМЕТРИЯ',
            'ПРОИЗВОДНАЯ  ФУНКЦИИ',
            'ГЕОМЕТРИЧЕСКИЕ  УТВЕРЖДЕНИЯ',
            'ПЛАНИМЕТРИЯ',
            'СТЕРЕОМЕТРИЯ'
        ]
        
        # Разбиваем текст на строки
        lines = text.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Проверяем, не новая ли тема (должна быть ДО заданий)
            if re.match(r'^[А-ЯЁ\s]{10,}$', line):
                # Нормализуем пробелы для сравнения
                normalized_line = ' '.join(line.split())
                # Проверяем, есть ли эта тема в списке валидных
                for valid_topic in valid_topics:
                    normalized_valid = ' '.join(valid_topic.split())
                    if normalized_line == normalized_valid or normalized_line in normalized_valid:
                        current_topic = normalized_line
                        self.stdout.write(self.style.WARNING(f'📚 Найдена тема: {current_topic}'))
                        break
                i += 1
                continue
            
            # Ищем начало задания (номер + текст)
            match = re.match(r'^(\d+)\s+(.+)', line)
            if match and current_topic:  # Парсим только если есть активная тема
                task_number = match.group(1)
                question_start = match.group(2)
                
                # Собираем полный вопрос
                question_lines = [question_start]
                i += 1
                
                # Читаем до варианта A) или А)
                while i < len(lines) and not re.match(r'^\s*[ABCDАВСDabcd]\)', lines[i]):
                    if lines[i].strip() and not re.match(r'^\d+\s+', lines[i]):
                        question_lines.append(lines[i].strip())
                    i += 1
                
                question = ' '.join(question_lines).strip()
                
                # Парсим варианты ответов
                options = {}
                cyrillic_to_latin = {'А': 'A', 'В': 'B', 'С': 'C', 'D': 'D'}
                
                # Читаем 4 варианта ответа
                for _ in range(4):
                    if i < len(lines):
                        # Поддержка A), B), C), D) и А), В), С), D)
                        option_match = re.match(r'^\s*([ABCDАВСDabcd])\)\s*(.+)', lines[i])
                        if option_match:
                            found_letter = option_match.group(1).upper()
                            # Конвертируем кириллицу в латиницу
                            if found_letter in cyrillic_to_latin:
                                found_letter = cyrillic_to_latin[found_letter]
                            options[found_letter] = option_match.group(2).strip()
                            i += 1
                        else:
                            break
                
                # Проверяем, что все варианты найдены
                if len(options) == 4 and question:
                    tasks.append({
                        'number': task_number,
                        'question': question,
                        'options': options,
                        'topic': current_topic
                    })
                    self.stdout.write(f'  ✓ Задание #{task_number}: {question[:60]}...')
            else:
                i += 1
        
        return tasks

    def save_tasks_to_db(self, tasks, subject_name):
        """Сохраняет задания в базу данных"""
        
        # Получаем или создаем предмет
        subject, created = Subject.objects.get_or_create(
            title=subject_name,
            defaults={
                'description': f'Подготовка к ЕГЭ по предмету {subject_name}',
                'icon': '📐' if subject_name == 'Математика' else '📚'
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f"✅ Создан предмет: {subject_name}"))
        
        # Группируем задания по темам
        topics_dict = {}
        for task in tasks:
            topic_title = task['topic']
            if topic_title not in topics_dict:
                topics_dict[topic_title] = []
            topics_dict[topic_title].append(task)
        
        # Создаем темы и задания
        for topic_title, topic_tasks in topics_dict.items():
            # Создаем или получаем тему
            topic, created = Topic.objects.get_or_create(
                title=topic_title,
                subject=subject,
                defaults={
                    'order': 1
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f"✅ Создана тема: {topic_title}"))
            
            # Создаем задания
            created_count = 0
            skipped_count = 0
            
            for task_data in topic_tasks:
                question = task_data['question']
                options = task_data['options']
                
                # Формируем JSON с вариантами ответов
                task_options = {
                    '1': options['A'],
                    '2': options['B'],
                    '3': options['C'],
                    '4': options['D']
                }
                
                # Правильный ответ нужно указать вручную или извлечь из PDF
                # Пока ставим первый вариант как заглушку
                correct_answer = "1"
                
                # Проверяем, существует ли уже такое задание
                existing_task = Task.objects.filter(
                    topic=topic,
                    question__icontains=question[:50]
                ).first()
                
                if not existing_task:
                    Task.objects.create(
                        subject=subject,
                        topic=topic,
                        question=question,
                        options=task_options,
                        correct_answer=correct_answer,
                        difficulty=1,
                        order=created_count + 1
                    )
                    created_count += 1
                else:
                    skipped_count += 1
            
            self.stdout.write(
                f"  📝 Тема '{topic_title}': создано {created_count}, пропущено {skipped_count}"
            )
