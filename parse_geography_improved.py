#!/usr/bin/env python3
"""
Улучшенный парсер для географии на основе логики парсера таджикского языка
"""

from __future__ import annotations

import json
import re
import subprocess
from collections import deque
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ParsedTask:
    number: int
    question: str
    options: dict[str, str]  # 1/2/3/4
    topic: str


_CYR_TO_LAT = {"А": "A", "В": "B", "С": "C", "D": "D"}
_LETTER_TO_NUMBER = {"A": "1", "B": "2", "C": "3", "D": "4"}


def run_pdftotext(pdf_path: Path, use_layout: bool = True) -> str:
    """Извлечение текста из PDF"""
    cmd = ["pdftotext"]
    if use_layout:
        cmd.append("-layout")
    cmd.extend([str(pdf_path), "-"])
    proc = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"pdftotext failed: {proc.stderr}")
    return proc.stdout or ""


def normalize_space(s: str) -> str:
    """Нормализация пробелов"""
    return re.sub(r"\s+", " ", s).strip()


def is_option_line(line: str) -> bool:
    """Проверка является ли строка вариантом ответа"""
    return bool(re.match(r"^\s*[ABCDАВСDabcd]\)\s+", line))


def is_question_number_line(line: str) -> int | None:
    """Проверка является ли строка номером вопроса"""
    m = re.match(r"^\s*(\d{1,4})\s*$", line)
    if not m:
        return None
    return int(m.group(1))


def match_question_start(line: str) -> tuple[int, str] | None:
    """Проверка строки типа: '1    Вопрос текст?'"""
    m = re.match(r"^\s*(\d{1,4})\s{1,}(.*\S.*)$", line)
    if not m:
        return None
    return int(m.group(1)), normalize_space(m.group(2))


def extract_options_from_raw_line(raw: str) -> tuple[str, dict[str, str]]:
    """
    Извлечение вариантов ответов из строки с inline опциями
    Например: '1   Вопрос?        А) вариант'
    """
    options: dict[str, str] = {}
    
    # Разделяем по большим пробелам (inline колонки)
    parts = re.split(r"\s{2,}", raw.strip())
    kept_parts: list[str] = []
    
    for part in parts:
        m = re.match(r"^\s*([ABCDАВСDabcd])\)\s*(.+)$", part)
        if m:
            letter = m.group(1).upper()
            letter = _CYR_TO_LAT.get(letter, letter)
            if letter in ("A", "B", "C", "D"):
                options[_LETTER_TO_NUMBER[letter]] = normalize_space(m.group(2))
            continue
        
        kept_parts.append(part)
    
    cleaned = normalize_space(" ".join(kept_parts))
    return cleaned, options


def is_topic_line(line: str) -> bool:
    """Проверка является ли строка заголовком темы"""
    if not line:
        return False
    if is_option_line(line):
        return False
    if re.match(r"^\d+\b", line):
        return False
    
    # Служебные строки
    noisy = {
        ".tj", "со РО", "мо Й", "на Г О", "и Н", "w !", "w", ".n", "tc", "Да", "р",
        "География", "Саҳифаи", "ИМД 2025", "НАМУНАИ", "САВОЛУ", "МАСЪАЛАҲО",
        "БО ИНТИХОБИ ЯК ҶАВОБИ ДУРУСТ"
    }
    
    for noise in noisy:
        if noise in line:
            return False
    
    # Темы обычно заглавными буквами и длинные
    if len(line) > 15 and line.isupper():
        return True
    
    # Или содержат ключевые слова
    topic_keywords = ["ГЕОГРАФИЯИ", "ГЕОГРАФИЯ"]
    for kw in topic_keywords:
        if kw in line:
            return True
    
    return False


def parse_geography_tasks(text: str) -> list[ParsedTask]:
    """
    Парсинг вопросов из Geography_tj.pdf
    
    Логика:
    1. Ищем номер вопроса или строку "номер + текст"
    2. Собираем текст вопроса до первого варианта
    3. Собираем 4 варианта ответа
    4. Отслеживаем текущую тему
    """
    lines = text.splitlines()
    tasks: list[ParsedTask] = []
    current_topic = "География"
    
    i = 0
    while i < len(lines):
        raw = lines[i]
        line = normalize_space(raw)
        
        # Пропускаем пустые строки
        if not line:
            i += 1
            continue
        
        # Проверка на тему
        if is_topic_line(line):
            current_topic = line
            i += 1
            continue
        
        # Проверка на строку "номер + текст вопроса"
        match_start = match_question_start(line)
        if match_start:
            number, q_first = match_start
            
            # Извлекаем inline опции из первой строки
            q_first_clean, inline_opts = extract_options_from_raw_line(raw)
            if inline_opts:
                # Пересоздаем q_first без inline опций
                match_start_clean = match_question_start(q_first_clean)
                if match_start_clean:
                    q_first = match_start_clean[1]
            
            q_lines = [q_first]
            i += 1
            
            # Собираем продолжение вопроса
            options: dict[str, str] = inline_opts.copy()
            
            while i < len(lines) and len(options) < 4:
                raw2 = lines[i]
                line2 = normalize_space(raw2)
                
                if not line2:
                    i += 1
                    continue
                
                # Если встретили вариант ответа
                if is_option_line(line2):
                    break
                
                # Если встретили следующий номер вопроса
                if is_question_number_line(line2) or match_question_start(line2):
                    break
                
                # Если встретили тему
                if is_topic_line(line2):
                    current_topic = line2
                    i += 1
                    continue
                
                # Извлекаем inline опции
                cleaned, opts = extract_options_from_raw_line(raw2)
                if opts:
                    options.update(opts)
                    if cleaned:
                        q_lines.append(cleaned)
                else:
                    q_lines.append(line2)
                
                i += 1
            
            # Собираем оставшиеся варианты ответов
            while i < len(lines) and len(options) < 4:
                raw3 = lines[i]
                line3 = normalize_space(raw3)
                
                if not line3:
                    i += 1
                    continue
                
                # Парсим вариант ответа
                m = re.match(r"^\s*([ABCDАВСDabcd])\)\s*(.+)$", raw3)
                if m:
                    letter = m.group(1).upper()
                    letter = _CYR_TO_LAT.get(letter, letter)
                    if letter in ("A", "B", "C", "D"):
                        options[_LETTER_TO_NUMBER[letter]] = normalize_space(m.group(2))
                    i += 1
                    continue
                
                # Если встретили следующий вопрос - выходим
                if is_question_number_line(line3) or match_question_start(line3):
                    break
                
                # Если встретили тему
                if is_topic_line(line3):
                    break
                
                i += 1
            
            # Сохраняем задачу
            question = normalize_space(" ".join(q_lines))
            if question and len(options) == 4:
                tasks.append(ParsedTask(
                    number=number,
                    question=question,
                    options=options,
                    topic=current_topic,
                ))
            continue
        
        # Проверка на отдельный номер вопроса
        num_only = is_question_number_line(line)
        if num_only is not None:
            number = num_only
            i += 1
            
            # Собираем текст вопроса
            q_lines: list[str] = []
            options: dict[str, str] = {}
            
            while i < len(lines) and len(options) < 4:
                raw4 = lines[i]
                line4 = normalize_space(raw4)
                
                if not line4:
                    i += 1
                    continue
                
                # Если встретили вариант ответа
                if is_option_line(line4):
                    break
                
                # Если встретили следующий номер
                if is_question_number_line(line4) or match_question_start(line4):
                    break
                
                # Если встретили тему
                if is_topic_line(line4):
                    current_topic = line4
                    i += 1
                    continue
                
                # Извлекаем inline опции
                cleaned, opts = extract_options_from_raw_line(raw4)
                if opts:
                    options.update(opts)
                    if cleaned:
                        q_lines.append(cleaned)
                else:
                    q_lines.append(line4)
                
                i += 1
            
            # Собираем варианты ответов
            while i < len(lines) and len(options) < 4:
                raw5 = lines[i]
                line5 = normalize_space(raw5)
                
                if not line5:
                    i += 1
                    continue
                
                m = re.match(r"^\s*([ABCDАВСDabcd])\)\s*(.+)$", raw5)
                if m:
                    letter = m.group(1).upper()
                    letter = _CYR_TO_LAT.get(letter, letter)
                    if letter in ("A", "B", "C", "D"):
                        options[_LETTER_TO_NUMBER[letter]] = normalize_space(m.group(2))
                    i += 1
                    continue
                
                # Если встретили следующий вопрос
                if is_question_number_line(line5) or match_question_start(line5):
                    break
                
                if is_topic_line(line5):
                    break
                
                i += 1
            
            # Сохраняем задачу
            question = normalize_space(" ".join(q_lines))
            if question and len(options) == 4:
                tasks.append(ParsedTask(
                    number=number,
                    question=question,
                    options=options,
                    topic=current_topic,
                ))
            continue
        
        i += 1
    
    return tasks


def parse_geography_answers(text: str) -> dict[int, str]:
    """Парсинг ответов из Geography_tj_key.pdf
    
    Формат: очередь номеров, затем очередь букв
    77
    78
    79
    ...
    C
    C
    A
    ...
    """
    answers: dict[int, str] = {}
    pending_numbers: deque[int] = deque()
    
    lines = text.splitlines()
    
    # Ищем начало ответов
    start_idx = 0
    for idx, line in enumerate(lines):
        if 'КАЛИДҲОИ' in line or 'ДУРУСТ' in line:
            start_idx = idx + 1
            break
    
    lines = lines[start_idx:]
    
    for raw_line in lines:
        line = raw_line.strip()
        
        if not line:
            continue
        
        # Пропускаем служебные строки
        if line in ['.tj', 'со РО', 'мо Й', 'на Г О', 'и Н', 'w !', 'w', '.n', 'tc', 'Да', 'р']:
            continue
        
        # Пропускаем заголовки
        if any(x in line for x in ['География', 'Саҳифаи', 'ИМД', 'КАЛИДҲОИ', 'САВОЛУ', 'МАСЪАЛАҲО']):
            continue
        
        # Номер вопроса
        if re.fullmatch(r'\d{1,4}', line):
            pending_numbers.append(int(line))
            continue
        
        # Буква ответа
        if re.fullmatch(r'[ABCDАВСD]', line):
            if pending_numbers:
                n = pending_numbers.popleft()
                letter = line.upper()
                letter = _CYR_TO_LAT.get(letter, letter)
                if letter in _LETTER_TO_NUMBER:
                    answers[n] = _LETTER_TO_NUMBER[letter]
            continue
    
    return answers


def generate_fixture(tasks: list[ParsedTask], answers: dict[int, str]) -> list[dict]:
    """Генерация Django fixture"""
    fixture = []
    
    # Определяем максимальные ID из существующих fixture файлов
    max_subject_id = 0
    max_topic_id = 0
    max_task_id = 0
    
    # Проверяем существующие fixture файлы
    for fixture_file in ["tjk_data.json", "geography_data.json"]:
        if Path(fixture_file).exists():
            try:
                with open(fixture_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    for item in existing_data:
                        if item['model'] == 'core.subject':
                            max_subject_id = max(max_subject_id, item['pk'])
                        elif item['model'] == 'core.topic':
                            max_topic_id = max(max_topic_id, item['pk'])
                        elif item['model'] == 'core.task':
                            max_task_id = max(max_task_id, item['pk'])
            except:
                pass
    
    # Используем следующие свободные ID
    subject_id = max_subject_id + 1
    topic_pk = max_topic_id
    task_pk = max_task_id
    
    # Предмет География
    fixture.append({
        "model": "core.subject",
        "pk": subject_id,
        "fields": {
            "title": "География",
            "icon": "🌍",
            "color": "#10B981"
        }
    })
    
    # Темы
    topics_map: dict[str, int] = {}
    
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
    
    # Задачи
    for task in tasks:
        task_pk += 1
        correct_answer = answers.get(task.number)
        if not correct_answer:
            print(f"⚠️  Нет ответа для вопроса {task.number}")
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
    
    return fixture


def main():
    print("🌍 Парсинг географии (улучшенная версия)...")
    print()
    
    # Извлекаем текст
    print("📄 Извлечение текста из Geography_tj.pdf...")
    tasks_text = run_pdftotext(Path("A3-2_Geography_tj.pdf"), use_layout=True)
    
    print("📄 Извлечение текста из Geography_tj_key.pdf...")
    answers_text = run_pdftotext(Path("A3-2_Geography_tj_key.pdf"), use_layout=False)
    
    # Парсим
    print("\n🔍 Парсинг вопросов...")
    tasks = parse_geography_tasks(tasks_text)
    print(f"   Найдено вопросов: {len(tasks)}")
    
    print("\n🔍 Парсинг ответов...")
    answers = parse_geography_answers(answers_text)
    print(f"   Найдено ответов: {len(answers)}")
    
    # Статистика
    topics_count: dict[str, int] = {}
    for task in tasks:
        topics_count[task.topic] = topics_count.get(task.topic, 0) + 1
    
    print("\n📊 Статистика по темам:")
    for topic, count in sorted(topics_count.items()):
        print(f"   {topic}: {count} вопросов")
    
    # Генерируем fixture
    print("\n📦 Генерация fixture...")
    fixture = generate_fixture(tasks, answers)
    
    # Сохраняем
    output_file = "geography_data.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(fixture, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Готово! Fixture сохранен в {output_file}")
    print(f"   Предметов: 1")
    print(f"   Тем: {len(topics_count)}")
    print(f"   Задач: {len([item for item in fixture if item['model'] == 'core.task'])}")
    print()
    print("📥 Для импорта в базу данных:")
    print(f"   python manage.py loaddata {output_file}")


if __name__ == '__main__':
    main()
