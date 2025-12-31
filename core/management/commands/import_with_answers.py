from django.core.management.base import BaseCommand
import re
import PyPDF2
from core.models import Subject, Topic, Task
import os

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    try:
        import google.generativeai as genai
        GENAI_AVAILABLE = True
    except ImportError:
        GENAI_AVAILABLE = False


class Command(BaseCommand):
    help = 'Импортирует задания с правильными ответами и очищает математические символы'

    def add_arguments(self, parser):
        parser.add_argument('tasks_pdf', type=str, help='PDF с заданиями')
        parser.add_argument('answers_pdf', type=str, help='PDF с ответами')
        parser.add_argument('--subject', type=str, default='Математика', help='Название предмета')

    def handle(self, *args, **options):
        tasks_pdf = options['tasks_pdf']
        answers_pdf = options['answers_pdf']
        subject_name = options['subject']
        
        # Настройка Gemini API
        api_key = os.getenv('GEMINI_API_KEY')
        if api_key and GENAI_AVAILABLE:
            try:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
                self.use_ai = True
                self.stdout.write(self.style.SUCCESS('✅ Gemini API подключен для очистки символов'))
            except Exception as e:
                self.use_ai = False
                self.stdout.write(self.style.WARNING(f'⚠️  Ошибка подключения Gemini: {e}'))
        else:
            self.use_ai = False
            self.stdout.write(self.style.WARNING('⚠️  Gemini API не настроен, очистка символов отключена'))
        
        self.stdout.write(self.style.SUCCESS(f'📖 Чтение заданий из: {tasks_pdf}'))
        tasks_text = self.extract_text_from_pdf(tasks_pdf)
        
        self.stdout.write(self.style.SUCCESS(f'📖 Чтение ответов из: {answers_pdf}'))
        answers_text = self.extract_text_from_pdf(answers_pdf)
        
        # Парсим задания
        self.stdout.write('🔍 Парсинг заданий...')
        tasks = self.parse_tasks_from_text(tasks_text)
        
        # Парсим ответы
        self.stdout.write('🔍 Парсинг ответов...')
        answers = self.parse_answers_from_text(answers_text)
        
        self.stdout.write(self.style.SUCCESS(f'✅ Найдено {len(tasks)} заданий'))
        self.stdout.write(self.style.SUCCESS(f'✅ Найдено {len(answers)} ответов'))
        
        # Объединяем задания с ответами
        self.stdout.write('🔗 Объединение заданий с ответами...')
        tasks_with_answers = self.merge_tasks_and_answers(tasks, answers)
        
        # Сохраняем в БД
        self.stdout.write('💾 Сохранение в базу данных...')
        self.save_tasks_to_db(tasks_with_answers, subject_name)
        
        self.stdout.write(self.style.SUCCESS('✅ Импорт завершен!'))

    def extract_text_from_pdf(self, pdf_path):
        """Извлекает текст из PDF"""
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ошибка: {e}"))
        return text

    def clean_math_symbols(self, text):
        """Очищает математические символы с помощью ИИ"""
        if not self.use_ai or not text:
            return text
        
        try:
            prompt = f"""Исправь математические символы в этом тексте, чтобы они правильно отображались.
Замени все непонятные символы на правильные математические обозначения.
Примеры замен:
- ሺ и ሻ → ( и )
- ൌ → =
- െ → -
- ൅ → +
- ∙ → ·
- √ и ට → √
- 𝒙, 𝒚, 𝒇 → x, y, f

Текст: {text}

Верни ТОЛЬКО исправленный текст без пояснений."""

            response = self.model.generate_content(prompt)
            cleaned = response.text.strip()
            return cleaned if cleaned else text
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'⚠️  Ошибка очистки: {e}'))
            return text

    def parse_tasks_from_text(self, text):
        """Парсит задания"""
        tasks = []
        current_topic = None
        
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
        
        lines = text.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Проверяем тему
            if re.match(r'^[А-ЯЁ\s]{10,}$', line):
                normalized_line = ' '.join(line.split())
                for valid_topic in valid_topics:
                    normalized_valid = ' '.join(valid_topic.split())
                    if normalized_line == normalized_valid or normalized_line in normalized_valid:
                        current_topic = normalized_line
                        break
                i += 1
                continue
            
            # Парсим задание
            match = re.match(r'^(\d+)\s+(.+)', line)
            if match and current_topic:
                task_number = match.group(1)
                question_start = match.group(2)
                
                question_lines = [question_start]
                i += 1
                
                while i < len(lines) and not re.match(r'^\s*[ABCDАВСDabcd]\)', lines[i]):
                    if lines[i].strip() and not re.match(r'^\d+\s+', lines[i]):
                        question_lines.append(lines[i].strip())
                    i += 1
                
                question = ' '.join(question_lines).strip()
                
                # Очищаем математические символы в вопросе
                question = self.clean_math_symbols(question)
                
                options = {}
                cyrillic_to_latin = {'А': 'A', 'В': 'B', 'С': 'C', 'D': 'D'}
                
                for _ in range(4):
                    if i < len(lines):
                        option_match = re.match(r'^\s*([ABCDАВСDabcd])\)\s*(.+)', lines[i])
                        if option_match:
                            found_letter = option_match.group(1).upper()
                            if found_letter in cyrillic_to_latin:
                                found_letter = cyrillic_to_latin[found_letter]
                            option_text = option_match.group(2).strip()
                            # Очищаем символы в вариантах ответа
                            option_text = self.clean_math_symbols(option_text)
                            options[found_letter] = option_text
                            i += 1
                        else:
                            break
                
                if len(options) == 4 and question:
                    tasks.append({
                        'number': task_number,
                        'question': question,
                        'options': options,
                        'topic': current_topic
                    })
            else:
                i += 1
        
        return tasks

    def parse_answers_from_text(self, text):
        """Парсит ответы из PDF с ответами"""
        answers = {}
        
        # Ищем паттерн: номер задания - буква ответа
        # Примеры: "1. A", "1) B", "1 - C", "1. А"
        lines = text.split('\n')
        
        for line in lines:
            # Паттерны для разных форматов
            patterns = [
                r'(\d+)\s*[.)\-:]\s*([ABCDАВСDabcd])',  # 1. A или 1) B
                r'(\d+)\s+([ABCDАВСDabcd])',  # 1 A
            ]
            
            for pattern in patterns:
                match = re.search(pattern, line)
                if match:
                    task_num = match.group(1)
                    answer_letter = match.group(2).upper()
                    
                    # Конвертируем кириллицу в латиницу
                    cyrillic_to_latin = {'А': 'A', 'В': 'B', 'С': 'C', 'D': 'D'}
                    if answer_letter in cyrillic_to_latin:
                        answer_letter = cyrillic_to_latin[answer_letter]
                    
                    # Конвертируем букву в номер (A=1, B=2, C=3, D=4)
                    letter_to_number = {'A': '1', 'B': '2', 'C': '3', 'D': '4'}
                    if answer_letter in letter_to_number:
                        answers[task_num] = letter_to_number[answer_letter]
                    break
        
        return answers

    def merge_tasks_and_answers(self, tasks, answers):
        """Объединяет задания с правильными ответами"""
        for task in tasks:
            task_num = task['number']
            if task_num in answers:
                task['correct_answer'] = answers[task_num]
            else:
                task['correct_answer'] = '1'  # По умолчанию
                self.stdout.write(self.style.WARNING(f'⚠️  Ответ не найден для задания #{task_num}'))
        
        return tasks

    def save_tasks_to_db(self, tasks, subject_name):
        """Сохраняет задания в БД"""
        subject, created = Subject.objects.get_or_create(
            title=subject_name,
            defaults={'icon': '📐'}
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f"✅ Создан предмет: {subject_name}"))
        
        # Группируем по темам
        topics_dict = {}
        for task in tasks:
            topic_title = task['topic']
            if topic_title not in topics_dict:
                topics_dict[topic_title] = []
            topics_dict[topic_title].append(task)
        
        # Создаем темы и задания
        for topic_title, topic_tasks in topics_dict.items():
            topic, created = Topic.objects.get_or_create(
                title=topic_title,
                subject=subject,
                defaults={'order': 1}
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f"✅ Создана тема: {topic_title}"))
            
            created_count = 0
            
            for task_data in topic_tasks:
                task_options = {
                    '1': task_data['options']['A'],
                    '2': task_data['options']['B'],
                    '3': task_data['options']['C'],
                    '4': task_data['options']['D']
                }
                
                Task.objects.create(
                    subject=subject,
                    topic=topic,
                    question=task_data['question'],
                    options=task_options,
                    correct_answer=task_data['correct_answer'],
                    difficulty=1,
                    order=created_count + 1
                )
                created_count += 1
            
            self.stdout.write(f"  📝 Тема '{topic_title}': создано {created_count} заданий")
