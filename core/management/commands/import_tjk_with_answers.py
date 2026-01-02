from __future__ import annotations

import re
import subprocess
from collections import deque
from dataclasses import dataclass

from django.core.management.base import BaseCommand

from core.models import Subject, Task, Topic


@dataclass
class ParsedTask:
    number: int
    question: str
    options: dict[str, str]
    topic: str
    correct_answer: str | None = None  # '1'..'4'


_CYR_TO_LAT = {"А": "A", "В": "B", "С": "C", "D": "D"}
_LETTER_TO_NUMBER = {"A": "1", "B": "2", "C": "3", "D": "4"}


def _run_pdftotext(pdf_path: str, first_page: int | None = None, last_page: int | None = None) -> str:
    cmd: list[str] = ["pdftotext", "-layout"]
    if first_page is not None:
        cmd += ["-f", str(first_page)]
    if last_page is not None:
        cmd += ["-l", str(last_page)]
    cmd += [pdf_path, "-"]

    proc = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if proc.returncode != 0:
        stderr = (proc.stderr or "").strip()
        raise RuntimeError(f"pdftotext failed (code={proc.returncode}): {stderr}")
    return proc.stdout or ""


def _normalize_space(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def _is_option_line(line: str) -> bool:
    return bool(re.match(r"^\s*[ABCDАВСDabcd]\)\s+", line))


def _is_question_number_line(line: str) -> int | None:
    m = re.match(r"^\s*(\d{1,4})\s*$", line)
    if not m:
        return None
    return int(m.group(1))


def _is_topic_line(line: str) -> bool:
    # Heuristic: uppercase Tajik/Cyrillic heading, no leading number, not option.
    if not line:
        return False
    if _is_option_line(line):
        return False
    if re.match(r"^\d+\b", line):
        return False

    # Remove common watermarks / noise
    noisy = {".tj", "Да", "р", "со РО", "мо Й", "на Г О", "и Н", "w !", "w", "w .n", "tc"}
    if line in noisy:
        return False

    # Topic lines often include commas and are mostly uppercase
    letters = re.findall(r"[A-Za-zА-ЯЁҒҚҲҶӢӮа-яёғқҳҷӣӯ]", line)
    if len(letters) < 8:
        return False

    upper_letters = [ch for ch in letters if ch == ch.upper()]
    if len(upper_letters) / max(1, len(letters)) < 0.7:
        return False

    # Exclude typical page headers
    if "Забони тоҷикӣ" in line:
        return False

    return True


def parse_tjk_tasks(tasks_text: str) -> list[ParsedTask]:
    lines = [ln.rstrip() for ln in tasks_text.splitlines()]

    tasks: list[ParsedTask] = []
    current_topic: str | None = None

    i = 0
    while i < len(lines):
        raw = lines[i]
        line = _normalize_space(raw)

        if _is_topic_line(line):
            current_topic = line
            i += 1
            continue

        num_only = _is_question_number_line(line)
        if num_only is not None:
            number = num_only
            i += 1

            # Collect question lines until first option
            q_lines: list[str] = []
            while i < len(lines):
                l = _normalize_space(lines[i])
                if not l:
                    i += 1
                    continue
                if _is_option_line(l):
                    break
                if _is_topic_line(l):
                    # topic changed unexpectedly, accept and stop question
                    current_topic = l
                    i += 1
                    continue
                q_lines.append(l)
                i += 1

            question = _normalize_space(" ".join(q_lines))

            options: dict[str, str] = {}
            for _ in range(8):  # allow some extra lines, but stop when got 4 options
                if i >= len(lines):
                    break
                lraw = lines[i]
                l = _normalize_space(lraw)
                m = re.match(r"^\s*([ABCDАВСDabcd])\)\s*(.+)$", lraw)
                if m:
                    letter = m.group(1).upper()
                    letter = _CYR_TO_LAT.get(letter, letter)
                    if letter in ("A", "B", "C", "D"):
                        options[letter] = _normalize_space(m.group(2))
                    i += 1
                    if len(options) == 4:
                        break
                    continue

                # Sometimes pdftotext merges option lines; try relaxed match
                m2 = re.match(r"^\s*([ABCDАВСDabcd])\)\s*(.+)$", l)
                if m2:
                    letter = m2.group(1).upper()
                    letter = _CYR_TO_LAT.get(letter, letter)
                    if letter in ("A", "B", "C", "D"):
                        options[letter] = _normalize_space(m2.group(2))
                    i += 1
                    if len(options) == 4:
                        break
                    continue

                # Not an option line; move on (could be footer/page header)
                i += 1

            if question and len(options) == 4:
                tasks.append(
                    ParsedTask(
                        number=number,
                        question=question,
                        options=options,
                        topic=current_topic or "Без темы",
                    )
                )
            continue

        i += 1

    return tasks


def parse_tjk_answers(answers_text: str) -> dict[int, str]:
    """Parses keys like:
    71\n72\n...\nA\nC\n...

    Returns mapping: question_number -> correct_answer ('1'..'4')
    """

    answers: dict[int, str] = {}
    pending_numbers: deque[int] = deque()

    lines = [re.sub(r"\s+", " ", ln).strip() for ln in answers_text.splitlines()]

    patterns = [
        re.compile(r"^(\d{1,4})\s*[.)\-:]\s*([ABCDАВСDabcd])$"),
        re.compile(r"^(\d{1,4})\s+([ABCDАВСDabcd])$"),
    ]

    for line in lines:
        if not line:
            continue

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
            # Queue-style format
            if re.fullmatch(r"\d{1,4}", line):
                pending_numbers.append(int(line))
                continue

            if re.fullmatch(r"[ABCDАВСD]", line):
                if pending_numbers:
                    n = pending_numbers.popleft()
                    letter = _CYR_TO_LAT.get(line.upper(), line.upper())
                    if letter in _LETTER_TO_NUMBER:
                        answers[n] = _LETTER_TO_NUMBER[letter]
                continue

    return answers


class Command(BaseCommand):
    help = 'Импортирует тесты по таджикскому языку из PDF + ключи, разбивая по темам'

    def add_arguments(self, parser):
        parser.add_argument('tasks_pdf', type=str, help='PDF с тестами (например TJK.pdf)')
        parser.add_argument('answers_pdf', type=str, help='PDF с ключами (например TJK_key.pdf)')
        parser.add_argument('--subject', type=str, default='Забони тоҷикӣ', help='Название предмета')
        parser.add_argument('--icon', type=str, default='🇹🇯', help='Иконка предмета')
        parser.add_argument('--dry-run', action='store_true', help='Только показать статистику, не сохранять в БД')

    def handle(self, *args, **options):
        tasks_pdf: str = options['tasks_pdf']
        answers_pdf: str = options['answers_pdf']
        subject_name: str = options['subject']
        subject_icon: str = options['icon']
        dry_run: bool = options['dry_run']

        self.stdout.write(self.style.SUCCESS(f'📄 Читаю тесты: {tasks_pdf}'))
        tasks_text = _run_pdftotext(tasks_pdf)

        self.stdout.write(self.style.SUCCESS(f'📄 Читаю ключи: {answers_pdf}'))
        answers_text = _run_pdftotext(answers_pdf)

        self.stdout.write(self.style.SUCCESS('🔍 Парсю задания...'))
        tasks = parse_tjk_tasks(tasks_text)
        self.stdout.write(self.style.SUCCESS(f'✅ Найдено заданий: {len(tasks)}'))

        self.stdout.write(self.style.SUCCESS('🔍 Парсю ответы...'))
        answers = parse_tjk_answers(answers_text)
        self.stdout.write(self.style.SUCCESS(f'✅ Найдено ключей: {len(answers)}'))

        # Merge answers
        missing = 0
        for t in tasks:
            t.correct_answer = answers.get(t.number)
            if not t.correct_answer:
                missing += 1

        if missing:
            self.stdout.write(self.style.WARNING(f'⚠️  Не найден ответ для {missing} заданий (они будут пропущены при сохранении).'))

        # Stats by topic
        topics_count: dict[str, int] = {}
        for t in tasks:
            topics_count[t.topic] = topics_count.get(t.topic, 0) + 1

        self.stdout.write('\n' + '=' * 80)
        self.stdout.write(self.style.SUCCESS('📊 СТАТИСТИКА ПО ТЕМАМ'))
        self.stdout.write('=' * 80)
        for topic, cnt in sorted(topics_count.items(), key=lambda x: (-x[1], x[0])):
            self.stdout.write(f' - {topic}: {cnt}')
        self.stdout.write('=' * 80 + '\n')

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN: в БД ничего не записано.'))
            return

        subject, created = Subject.objects.get_or_create(
            title=subject_name,
            defaults={
                'icon': subject_icon,
                'color': '#6366F1',
            },
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'✅ Создан предмет: {subject.title}'))

        # Create topics in stable order (appearance)
        topic_order = 1
        topic_objs: dict[str, Topic] = {}

        def get_topic(title: str) -> Topic:
            nonlocal topic_order
            if title in topic_objs:
                return topic_objs[title]
            topic, _ = Topic.objects.get_or_create(
                subject=subject,
                title=title,
                defaults={'order': topic_order, 'is_locked': False},
            )
            topic_order += 1
            topic_objs[title] = topic
            return topic

        # Save tasks grouped by topic, preserve original question numbering order
        tasks_sorted = sorted(tasks, key=lambda t: (t.topic, t.number))

        created_tasks = 0
        skipped_tasks = 0
        skipped_no_answer = 0

        per_topic_order: dict[str, int] = {}

        for t in tasks_sorted:
            if not t.correct_answer:
                skipped_no_answer += 1
                continue

            topic = get_topic(t.topic)
            per_topic_order[topic.title] = per_topic_order.get(topic.title, 0) + 1
            order = per_topic_order[topic.title]

            options_db = {
                '1': t.options['A'],
                '2': t.options['B'],
                '3': t.options['C'],
                '4': t.options['D'],
            }

            # Dedup by (topic, question prefix)
            existing = Task.objects.filter(topic=topic, question__startswith=t.question[:80]).first()
            if existing:
                skipped_tasks += 1
                continue

            Task.objects.create(
                subject=subject,
                topic=topic,
                question=t.question,
                options=options_db,
                correct_answer=t.correct_answer,
                difficulty=1,
                order=order,
            )
            created_tasks += 1

        self.stdout.write(self.style.SUCCESS(f'✅ Импорт завершен: создано {created_tasks}, пропущено дублей {skipped_tasks}, без ответа {skipped_no_answer}'))
