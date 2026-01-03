#!/usr/bin/env python3
"""
Парсер для географии (A3-2_Geography_tj.pdf и A3-2_Geography_tj_key.pdf)
Использует ту же логику что и для таджикского языка
"""

import re
import json
import subprocess
from collections import deque
from typing import NamedTuple

# Маппинг кириллических букв в латинские
_CYR_TO_LAT = {
    'А': 'A', 'В': 'B', 'С': 'C', 'D': 'D',
    'а': 'A', 'в': 'B', 'с': 'C', 'd': 'D',
}

# Маппинг букв в цифры (1-4)
_LETTER_TO_NUMBER = {
    'A': '1', 'B': '2', 'C': '3', 'D': '4',
}


class ParsedTask(NamedTuple):
    number: int
    question: str
    options: dict[str, str]
    topic: str


def _normalize_space(text: str) -> str:
    """Нормализация пробелов"""
    return re.sub(r'\s+', ' ', text).strip()


def _is_topic_line(line: str) -> bool:
    """Проверка является ли строка заголовком темы"""
    # Темы обычно написаны заглавными буквами
    if not line:
        return False
    
    # Примеры тем из географии
    topic_patterns = [
        r'^ГЕОГРАФИЯИ ТАБИИИ УМУМӢ',
        r'^ГЕОГРАФИЯИ',
        r'^[А-ЯЁ\s]{10,}$',  # Строка из заглавных букв
    ]
    
    for pattern in topic_patterns:
        if re.match(pattern, line):
            return True
    
    return False


def _is_question_number_line(line: str) -> int | None:
    """Проверка является ли строка номером вопроса"""
    # Номер вопроса - это просто число
    if re.fullmatch(r'\d{1,4}', line):
        return int(line)
    return None


def _is_option_line(line: str) -> bool:
    """Проверка является ли строка вариантом ответа"""
    # Варианты начинаются с A), B), C), D)
    return bool(re.match(r'^\s*[ABCDАВСDabcd]\)', line))


def parse_geography_tasks(tasks_text: str) -> list[ParsedTask]:
    """
    Парсинг вопросов из Geography_tj.pdf
    
    Структура:
    - Темы (заголовки заглавными буквами)
    - Номер вопроса (число) ИЛИ вопрос без номера (первый после темы)
    - Текст вопроса (несколько строк)
    - Варианты A), B), C), D)
    """
    lines = [ln.rstrip() for ln in tasks_text.splitlines()]
    
    tasks: list[ParsedTask] = []
    current_topic: str | None = None
    question_counter = 1  # Счетчик для вопросов без номера
    
    i = 0
    while i < len(lines):
        raw = lines[i]
        line = _normalize_space(raw)
        
        # Пропускаем служебные строки
        if not line or line in ['.tj', 'со РО', 'мо Й', 'на Г О', 'и Н', 'w !', 'w', '.n', 'tc', 'Да', 'р']:
            i += 1
            continue
        
        # Пропускаем заголовки и номера страниц
        if 'География' in line or 'Саҳифаи' in line or 'ИМД 2025' in line or 'НАМУНАИ' in line or 'САВОЛУ' in line:
            i += 1
            continue
        
        # Проверка на тему
        if _is_topic_line(line):
            current_topic = line
            i += 1
            
            # После темы может идти вопрос БЕЗ номера
            # Проверяем следующие строки
            if i < len(lines):
                next_line = _normalize_space(lines[i])
                # Если следующая строка не число и не пустая - это вопрос без номера
                if next_line and not re.fullmatch(r'\d{1,4}', next_line) and not next_line in ['.tj', 'со РО', 'мо Й', 'на Г О', 'и Н', 'w !', 'w', '.n', 'tc', 'Да', 'р']:
                    # Это вопрос без номера, используем счетчик
                    number = question_counter
                    question_counter += 1
                    
                    # Собираем текст вопроса
                    q_lines: list[str] = []
                    while i < len(lines):
                        l = _normalize_space(lines[i])
                        
                        if not l or l in ['.tj', 'со РО', 'мо Й', 'на Г О', 'и Н', 'w !', 'w', '.n', 'tc', 'Да', 'р']:
                            i += 1
                            continue
                        
                        if _is_option_line(l):
                            break
                        
                        if _is_topic_line(l):
                            break
                        
                        # Если встретили число - это может быть следующий вопрос
                        if re.fullmatch(r'\d{1,4}', l):
                            break
                        
                        q_lines.append(l)
                        i += 1
                    
                    question = _normalize_space(" ".join(q_lines))
                    
                    # Собираем варианты
                    options: dict[str, str] = {}
                    for _ in range(10):
                        if i >= len(lines):
                            break
                        
                        lraw = lines[i]
                        l = _normalize_space(lraw)
                        
                        if not l or l in ['.tj', 'со РО', 'мо Й', 'на Г О', 'и Н', 'w !', 'w', '.n', 'tc', 'Да', 'р']:
                            i += 1
                            continue
                        
                        m = re.match(r'^\s*([ABCDАВСDabcd])\)\s*(.+)$', lraw)
                        if m:
                            letter = m.group(1).upper()
                            letter = _CYR_TO_LAT.get(letter, letter)
                            if letter in ('A', 'B', 'C', 'D'):
                                options[_LETTER_TO_NUMBER[letter]] = _normalize_space(m.group(2))
                            i += 1
                            if len(options) == 4:
                                break
                            continue
                        
                        # Не вариант - выходим
                        if not _is_option_line(l):
                            break
                        i += 1
                    
                    if question and len(options) == 4:
                        tasks.append(ParsedTask(
                            number=number,
                            question=question,
                            options=options,
                            topic=current_topic or "География",
                        ))
            continue
        
        # Проверка на номер вопроса
        num_only = _is_question_number_line(line)
        if num_only is not None:
            number = num_only
            question_counter = number + 1  # Обновляем счетчик
            i += 1
            
            # Собираем текст вопроса до первого варианта
            q_lines: list[str] = []
            while i < len(lines):
                l = _normalize_space(lines[i])
                
                # Пропускаем пустые и служебные строки
                if not l or l in ['.tj', 'со РО', 'мо Й', 'на Г О', 'и Н', 'w !', 'w', '.n', 'tc', 'Да', 'р']:
                    i += 1
                    continue
                
                # Если встретили вариант ответа - останавливаемся
                if _is_option_line(l):
                    break
                
                # Если встретили новую тему
                if _is_topic_line(l):
                    current_topic = l
                    i += 1
                    continue
                
                # Если встретили номер следующего вопроса
                if re.fullmatch(r'\d{1,4}', l):
                    break
                
                q_lines.append(l)
                i += 1
            
            question = _normalize_space(" ".join(q_lines))
            
            # Собираем варианты ответов
            options: dict[str, str] = {}
            for _ in range(15):  # Увеличиваем попытки
                if i >= len(lines):
                    break
                
                lraw = lines[i]
                l = _normalize_space(lraw)
                
                # Пропускаем служебные строки
                if not l or l in ['.tj', 'со РО', 'мо Й', 'на Г О', 'и Н', 'w !', 'w', '.n', 'tc', 'Да', 'р']:
                    i += 1
                    continue
                
                # Парсим вариант ответа
                m = re.match(r'^\s*([ABCDАВСDabcd])\)\s*(.+)$', lraw)
                if m:
                    letter = m.group(1).upper()
                    letter = _CYR_TO_LAT.get(letter, letter)
                    if letter in ('A', 'B', 'C', 'D'):
                        options[_LETTER_TO_NUMBER[letter]] = _normalize_space(m.group(2))
                    i += 1
                    if len(options) == 4:
                        break
                    continue
                
                # Попытка распарсить слитные варианты
                m2 = re.match(r'^\s*([ABCDАВСDabcd])\)\s*(.+)$', l)
                if m2:
                    letter = m2.group(1).upper()
                    letter = _CYR_TO_LAT.get(letter, letter)
                    if letter in ('A', 'B', 'C', 'D'):
                        options[_LETTER_TO_NUMBER[letter]] = _normalize_space(m2.group(2))
                    i += 1
                    if len(options) == 4:
                        break
                    continue
                
                # Если встретили номер следующего вопроса - выходим
                if re.fullmatch(r'\d{1,4}', l):
                    break
                
                # Не вариант ответа - пропускаем
                i += 1
            
            # Сохраняем задачу если есть вопрос и 4 варианта
            if question and len(options) == 4:
                tasks.append(ParsedTask(
                    number=number,
                    question=question,
                    options=options,
                    topic=current_topic or "География",
                ))
            continue
        
        i += 1
    
    return tasks


def parse_geography_answers(answers_text: str) -> dict[int, str]:
    """
    Парсинг ответов из Geography_tj_key.pdf
    
    Формат:
    77  C
    78  C
    79  A
    ...
    """
    answers: dict[int, str] = {}
    pending_numbers: deque[int] = deque()
    
    lines = [re.sub(r'\s+', ' ', ln).strip() for ln in answers_text.splitlines()]
    
    # Ищем начало ответов (после "КАЛИДҲОИ")
    start_idx = 0
    for idx, line in enumerate(lines):
        if 'КАЛИДҲОИ' in line or 'ДУРУСТ' in line:
            start_idx = idx + 1
            break
    
    lines = lines[start_idx:]
    
    # Паттерны для парсинга
    patterns = [
        re.compile(r'^(\d{1,4})\s*[.)\-:]\s*([ABCDАВСDabcd])$'),
        re.compile(r'^(\d{1,4})\s+([ABCDАВСDabcd])$'),
    ]
    
    for line in lines:
        if not line or line in ['.tj', 'со РО', 'мо Й', 'на Г О', 'и Н', 'w !', 'w', '.n', 'tc', 'Да', 'р']:
            continue
        
        # Попытка распарсить формат "номер буква"
        for pat in patterns:
            m = pat.match(line)
            if m:
                n = int(m.group(1))
                letter = m.group(2).upper()
                letter = _CYR_TO_LAT.get(letter, letter)
                if letter in _LETTER_TO_NUMBER:
                    answers[n] = _LETTER_TO_NUMBER[letter]
                break
        else:
            # Формат с очередью: сначала номера, потом буквы
            if re.fullmatch(r'\d{1,4}', line):
                pending_numbers.append(int(line))
                continue
            
            if re.fullmatch(r'[ABCDАВСD]', line):
                if pending_numbers:
                    n = pending_numbers.popleft()
                    letter = _CYR_TO_LAT.get(line.upper(), line.upper())
                    if letter in _LETTER_TO_NUMBER:
                        answers[n] = _LETTER_TO_NUMBER[letter]
                continue
    
    return answers


def generate_fixture(tasks: list[ParsedTask], answers: dict[int, str]) -> list[dict]:
    """
    Генерация Django fixture в формате JSON
    
    Структура:
    - Subject: География (id=5)
    - Topics: по темам из PDF
    - Tasks: все вопросы с ответами
    """
    fixture = []
    
    # 1. Создаем предмет "География"
    subject_id = 5  # ID для географии
    fixture.append({
        "model": "core.subject",
        "pk": subject_id,
        "fields": {
            "title": "География",
            "icon": "🌍",
            "color": "#10B981"
        }
    })
    
    # 2. Собираем уникальные темы
    topics_map: dict[str, int] = {}
    topic_pk = 50  # Начальный ID для тем географии
    
    for task in tasks:
        if task.topic and task.topic not in topics_map:
            topics_map[task.topic] = topic_pk
            fixture.append({
                "model": "core.topic",
                "pk": topic_pk,
                "fields": {
                    "subject": subject_id,
                    "title": task.topic,
                    "order": len(topics_map),
                    "is_locked": False
                }
            })
            topic_pk += 1
    
    # 3. Создаем задачи
    task_pk = 5000  # Начальный ID для задач географии
    
    for task in tasks:
        correct_answer = answers.get(task.number)
        if not correct_answer:
            print(f"⚠️  Предупреждение: нет ответа для вопроса {task.number}")
            continue
        
        topic_id = topics_map.get(task.topic)
        
        fixture.append({
            "model": "core.task",
            "pk": task_pk,
            "fields": {
                "subject": subject_id,
                "topic": topic_id,
                "question": task.question,
                "options": task.options,
                "correct_answer": correct_answer,
                "difficulty": 1,
                "order": task.number
            }
        })
        task_pk += 1
    
    return fixture


def main():
    """Основная функция"""
    print("🌍 Парсинг географии...")
    print()
    
    # Извлекаем текст из PDF
    print("📄 Извлечение текста из Geography_tj.pdf...")
    tasks_text = subprocess.check_output(
        ['pdftotext', 'A3-2_Geography_tj.pdf', '-'],
        text=True
    )
    
    print("📄 Извлечение текста из Geography_tj_key.pdf...")
    answers_text = subprocess.check_output(
        ['pdftotext', 'A3-2_Geography_tj_key.pdf', '-'],
        text=True
    )
    
    # Парсим
    print("\n🔍 Парсинг вопросов...")
    tasks = parse_geography_tasks(tasks_text)
    print(f"   Найдено вопросов: {len(tasks)}")
    
    print("\n🔍 Парсинг ответов...")
    answers = parse_geography_answers(answers_text)
    print(f"   Найдено ответов: {len(answers)}")
    
    # Статистика по темам
    topics_count: dict[str, int] = {}
    for task in tasks:
        topics_count[task.topic] = topics_count.get(task.topic, 0) + 1
    
    print("\n📊 Статистика по темам:")
    for topic, count in topics_count.items():
        print(f"   {topic}: {count} вопросов")
    
    # Генерируем fixture
    print("\n📦 Генерация fixture...")
    fixture = generate_fixture(tasks, answers)
    
    # Сохраняем в файл
    output_file = "geography_data.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(fixture, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Готово! Fixture сохранен в {output_file}")
    print(f"   Предметов: 1")
    print(f"   Тем: {len(topics_count)}")
    print(f"   Задач: {len([item for item in fixture if item['model'] == 'core.task'])}")
    print()
    print("📥 Для импорта в базу данных выполните:")
    print(f"   python manage.py loaddata {output_file}")


if __name__ == '__main__':
    main()
