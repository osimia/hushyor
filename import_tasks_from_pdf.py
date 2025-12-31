import os
import django
import re
import PyPDF2

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from core.models import Subject, Topic, Task


def extract_text_from_pdf(pdf_path):
    """Извлекает текст из PDF файла"""
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text()
    except Exception as e:
        print(f"Ошибка при чтении PDF: {e}")
    return text


def parse_tasks_from_text(text):
    """Парсит задания из текста"""
    tasks = []
    
    # Ищем все темы в тексте
    topics = re.findall(r'([А-ЯЁ\s]+(?:ЧИСЛАМИ|ВЫРАЖЕНИЯМИ|УРАВНЕНИЯМИ))', text)
    current_topic = "Действия с рациональными и иррациональными числами"
    
    # Разбиваем текст на строки для более точного парсинга
    lines = text.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Проверяем, начинается ли строка с номера задания
        match = re.match(r'^(\d+)\s+(.+)', line)
        if match:
            task_number = match.group(1)
            question_start = match.group(2)
            
            # Собираем полный вопрос (может быть на нескольких строках)
            question_lines = [question_start]
            i += 1
            
            # Читаем до варианта A)
            while i < len(lines) and not re.match(r'^\s*A\)', lines[i]):
                if lines[i].strip() and not re.match(r'^\d+\s+', lines[i]):
                    question_lines.append(lines[i].strip())
                i += 1
            
            question = ' '.join(question_lines).strip()
            
            # Парсим варианты ответов
            options = {}
            for option_letter in ['A', 'B', 'C', 'D']:
                if i < len(lines):
                    option_match = re.match(rf'^\s*{option_letter}\)\s*(.+)', lines[i])
                    if option_match:
                        options[option_letter] = option_match.group(1).strip()
                        i += 1
            
            # Проверяем, что все варианты найдены
            if len(options) == 4:
                tasks.append({
                    'number': task_number,
                    'question': question,
                    'options': options,
                    'topic': current_topic
                })
        else:
            i += 1
    
    return tasks


def save_tasks_to_db(tasks, subject_name='Математика'):
    """Сохраняет задания в базу данных"""
    
    # Получаем или создаем предмет
    subject, created = Subject.objects.get_or_create(
        title=subject_name,
        defaults={
            'description': 'Подготовка к ЕГЭ по математике',
            'icon': '📐'
        }
    )
    
    if created:
        print(f"✅ Создан предмет: {subject_name}")
    
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
                'difficulty': 'easy',
                'order': 1
            }
        )
        
        if created:
            print(f"✅ Создана тема: {topic_title}")
        
        # Создаем задания
        for task_data in topic_tasks:
            question = task_data['question']
            options = task_data['options']
            
            # Формируем текст вопроса с вариантами
            full_question = f"{question}\n\n"
            full_question += f"A) {options['A']}\n"
            full_question += f"B) {options['B']}\n"
            full_question += f"C) {options['C']}\n"
            full_question += f"D) {options['D']}"
            
            # Пока не знаем правильный ответ, ставим заглушку
            # В реальности нужно извлечь из PDF или указать вручную
            correct_answer = "A"  # Заглушка
            
            # Проверяем, существует ли уже такое задание
            existing_task = Task.objects.filter(
                topic=topic,
                question__icontains=question[:50]  # Проверяем по началу вопроса
            ).first()
            
            if not existing_task:
                task = Task.objects.create(
                    topic=topic,
                    question=full_question,
                    correct_answer=correct_answer,
                    difficulty='easy',
                    points=5
                )
                print(f"✅ Создано задание #{task_data['number']}: {question[:50]}...")
            else:
                print(f"⏭️  Задание уже существует: {question[:50]}...")


def main():
    """Основная функция"""
    pdf_path = 'A2-12_Math_ru.pdf'
    
    print("📖 Чтение PDF файла...")
    text = extract_text_from_pdf(pdf_path)
    
    if not text:
        print("❌ Не удалось извлечь текст из PDF")
        return
    
    print(f"✅ Извлечено {len(text)} символов")
    
    print("\n🔍 Парсинг заданий...")
    tasks = parse_tasks_from_text(text)
    
    print(f"✅ Найдено {len(tasks)} заданий")
    
    if tasks:
        print("\n💾 Сохранение в базу данных...")
        save_tasks_to_db(tasks)
        print("\n✅ Импорт завершен!")
    else:
        print("\n⚠️  Задания не найдены. Проверьте формат PDF.")
        print("\nПервые 500 символов текста:")
        print(text[:500])


if __name__ == '__main__':
    main()
