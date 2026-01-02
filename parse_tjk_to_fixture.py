from __future__ import annotations

import argparse
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
    options: dict[str, str]  # A/B/C/D
    topic: str
    correct_answer: str  # '1'..'4'


_CYR_TO_LAT = {"А": "A", "В": "B", "С": "C", "D": "D"}
_LETTER_TO_NUMBER = {"A": "1", "B": "2", "C": "3", "D": "4"}


def run_pdftotext(pdf_path: Path, first_page: int | None = None, last_page: int | None = None) -> str:
    cmd: list[str] = ["pdftotext", "-layout"]
    if first_page is not None:
        cmd += ["-f", str(first_page)]
    if last_page is not None:
        cmd += ["-l", str(last_page)]
    cmd += [str(pdf_path), "-"]

    proc = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if proc.returncode != 0:
        stderr = (proc.stderr or "").strip()
        raise RuntimeError(f"pdftotext failed (code={proc.returncode}): {stderr}")
    return proc.stdout or ""


def normalize_space(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def is_option_line(line: str) -> bool:
    return bool(re.match(r"^\s*[ABCDАВСDabcd]\)\s+", line))


def is_question_number_line(line: str) -> int | None:
    m = re.match(r"^\s*(\d{1,4})\s*$", line)
    if not m:
        return None
    return int(m.group(1))


def match_question_start(line: str) -> tuple[int, str] | None:
    """Matches lines like: '1    Дар кадом ... ?'"""
    m = re.match(r"^\s*(\d{1,4})\s{1,}(.*\S.*)$", line)
    if not m:
        return None
    return int(m.group(1)), normalize_space(m.group(2))


def extract_options_from_raw_line(raw: str) -> tuple[str, dict[str, str]]:
    """Extracts options from a single raw pdftotext line.

    In TJK.pdf a question line can contain an inline option fragment, e.g.:
    '1   ...?        А) саҳро'
    We return cleaned line (with option fragments removed) + found options.
    """
    options: dict[str, str] = {}

    # Split by large gaps to separate inline columns
    parts = re.split(r"\s{2,}", raw.strip())
    kept_parts: list[str] = []

    for part in parts:
        m = re.match(r"^\s*([ABCDАВСDabcd])\)\s*(.+)$", part)
        if m:
            letter = m.group(1).upper()
            letter = _CYR_TO_LAT.get(letter, letter)
            if letter in ("A", "B", "C", "D"):
                options[letter] = normalize_space(m.group(2))
            continue

        kept_parts.append(part)

    cleaned = normalize_space(" ".join(kept_parts))
    return cleaned, options


def is_topic_line(line: str) -> bool:
    if not line:
        return False
    if is_option_line(line):
        return False
    if re.match(r"^\d+\b", line):
        return False

    # Noise lines from PDF watermarking
    noisy = {
        ".tj",
        "Да",
        "р",
        "со РО",
        "мо Й",
        "на Г О",
        "и Н",
        "w !",
        "w",
        "w .n",
        "tc",
    }
    if line in noisy:
        return False

    # Exclude repeated page header
    if "Забони тоҷикӣ" in line:
        return False

    letters = re.findall(r"[A-Za-zА-ЯЁҒҚҲҶӢӮа-яёғқҳҷӣӯ]", line)
    if len(letters) < 10:
        return False

    upper_letters = [ch for ch in letters if ch == ch.upper()]
    ratio = len(upper_letters) / max(1, len(letters))

    # Tajik topics often appear in uppercase; allow some mixed case.
    if ratio < 0.6:
        return False

    # Topic lines tend to be long and descriptive
    return len(line) >= 12


def parse_tasks(tasks_text: str) -> list[tuple[int, str, dict[str, str], str]]:
    lines = [ln.rstrip("\n") for ln in tasks_text.splitlines()]

    tasks: list[tuple[int, str, dict[str, str], str]] = []
    current_topic: str | None = None

    i = 0
    while i < len(lines):
        raw = lines[i]
        line = normalize_space(raw)

        if is_topic_line(line):
            current_topic = line
            i += 1
            continue

        q_start = match_question_start(raw)
        if q_start is not None:
            number, first_q = q_start

            first_q_clean, inline_options = extract_options_from_raw_line(raw)
            if first_q_clean:
                first_q = first_q_clean
            i += 1

            # Collect question until first option
            q_lines: list[str] = [first_q]
            while i < len(lines):
                l = normalize_space(lines[i])
                if not l:
                    i += 1
                    continue
                if is_option_line(l):
                    break
                if is_topic_line(l):
                    current_topic = l
                    i += 1
                    continue
                if match_question_start(lines[i]) is not None:
                    break
                q_lines.append(l)
                i += 1

            question = normalize_space(" ".join(q_lines))

            options: dict[str, str] = {}
            options.update(inline_options)
            # Read options; stop when got 4.
            while i < len(lines) and len(options) < 4:
                lraw = lines[i]
                m = re.match(r"^\s*([ABCDАВСDabcd])\)\s*(.+)$", lraw)
                if m:
                    letter = m.group(1).upper()
                    letter = _CYR_TO_LAT.get(letter, letter)
                    if letter in ("A", "B", "C", "D"):
                        options[letter] = normalize_space(m.group(2))
                    i += 1
                    continue

                # Inline options can appear in the same line as other text
                _, inline = extract_options_from_raw_line(lraw)
                if inline:
                    options.update(inline)
                    i += 1
                    continue

                l = normalize_space(lraw)
                # Skip non-option noise / headers
                if not l or is_topic_line(l) or is_question_number_line(l) is not None:
                    break
                i += 1

            if question and len(options) == 4:
                tasks.append((number, question, options, current_topic or "Без темы"))
            continue

        i += 1

    return tasks


def parse_answers(answers_text: str) -> dict[int, str]:
    """Parse answer keys from TJK_key.pdf.

    The PDF often contains a column of question numbers followed by a column of letters.
    We tokenize a stream of integers and letters and pair them FIFO.
    """
    answers: dict[int, str] = {}
    pending_numbers: deque[int] = deque()

    # Start after the key section to avoid picking up page numbers / 2025 / etc
    start_idx = answers_text.find('КАЛИД')
    if start_idx != -1:
        answers_text = answers_text[start_idx:]

    # Normalize and tokenize numbers/letters
    normalized = re.sub(r"\s+", " ", answers_text)
    tokens = re.findall(r"\b\d{1,4}\b|\b[ABCD]\b|\b[АВСD]\b", normalized, flags=re.IGNORECASE)

    for tok in tokens:
        if tok.isdigit():
            n = int(tok)
            # Ignore unrelated numbers
            if 1 <= n <= 500:
                pending_numbers.append(n)
            continue

        letter = tok.upper()
        letter = _CYR_TO_LAT.get(letter, letter)
        if letter not in _LETTER_TO_NUMBER:
            continue

        if pending_numbers:
            n = pending_numbers.popleft()
            answers[n] = _LETTER_TO_NUMBER[letter]

    return answers


def find_max_pks(existing_fixture: list[dict]) -> dict[str, int]:
    maxes = {
        "core.subject": 0,
        "core.topic": 0,
        "core.task": 0,
    }
    for row in existing_fixture:
        model = row.get("model")
        pk = int(row.get("pk", 0) or 0)
        if model in maxes:
            maxes[model] = max(maxes[model], pk)
    return maxes


def main() -> int:
    parser = argparse.ArgumentParser(description="Parse TJK IMD 2025 PDFs to Django fixture JSON")
    parser.add_argument("--tasks", default="TJK.pdf", help="Path to tasks PDF")
    parser.add_argument("--keys", default="TJK_key.pdf", help="Path to keys PDF")
    parser.add_argument("--out", default="tjk_data.json", help="Output fixture json")
    parser.add_argument("--base-fixture", default="hushyor_data.json", help="Existing fixture to avoid PK collisions")
    parser.add_argument("--subject-title", default="Забони тоҷикӣ", help="Subject title")
    parser.add_argument("--subject-icon", default="🇹🇯", help="Subject icon")
    parser.add_argument("--subject-color", default="#10B981", help="Subject color")
    args = parser.parse_args()

    base = Path(__file__).resolve().parent
    tasks_pdf = (base / args.tasks).resolve() if not Path(args.tasks).is_absolute() else Path(args.tasks)
    keys_pdf = (base / args.keys).resolve() if not Path(args.keys).is_absolute() else Path(args.keys)
    out_path = (base / args.out).resolve() if not Path(args.out).is_absolute() else Path(args.out)
    base_fixture_path = (base / args.base_fixture).resolve() if not Path(args.base_fixture).is_absolute() else Path(args.base_fixture)

    base_fixture: list[dict] = []
    if base_fixture_path.exists():
        base_fixture = json.loads(base_fixture_path.read_text(encoding="utf-8"))

    maxes = find_max_pks(base_fixture)

    tasks_text = run_pdftotext(tasks_pdf)
    keys_text = run_pdftotext(keys_pdf)

    tasks_raw = parse_tasks(tasks_text)
    answers = parse_answers(keys_text)

    merged: list[ParsedTask] = []
    for number, question, options, topic in tasks_raw:
        correct = answers.get(number)
        if not correct:
            continue
        merged.append(
            ParsedTask(
                number=number,
                question=question,
                options=options,
                topic=topic,
                correct_answer=correct,
            )
        )

    # Build fixture
    subject_pk = maxes["core.subject"] + 1
    topic_pk = maxes["core.topic"]
    task_pk = maxes["core.task"]

    fixture_out: list[dict] = []
    fixture_out.append(
        {
            "model": "core.subject",
            "pk": subject_pk,
            "fields": {
                "title": args.subject_title,
                "icon": args.subject_icon,
                "color": args.subject_color,
            },
        }
    )

    # Create topics in first-seen order
    topic_map: dict[str, int] = {}
    topic_order = 1

    for t in merged:
        if t.topic not in topic_map:
            topic_pk += 1
            topic_map[t.topic] = topic_pk
            fixture_out.append(
                {
                    "model": "core.topic",
                    "pk": topic_pk,
                    "fields": {
                        "subject": subject_pk,
                        "title": t.topic,
                        "order": topic_order,
                        "is_locked": False,
                    },
                }
            )
            topic_order += 1

    # Tasks per topic order
    per_topic_order: dict[int, int] = {}
    for t in sorted(merged, key=lambda x: (topic_map[x.topic], x.number)):
        task_pk += 1
        tp = topic_map[t.topic]
        per_topic_order[tp] = per_topic_order.get(tp, 0) + 1

        fixture_out.append(
            {
                "model": "core.task",
                "pk": task_pk,
                "fields": {
                    "subject": subject_pk,
                    "topic": tp,
                    "question": t.question,
                    "options": {
                        "1": t.options["A"],
                        "2": t.options["B"],
                        "3": t.options["C"],
                        "4": t.options["D"],
                    },
                    "correct_answer": t.correct_answer,
                    "difficulty": 1,
                    "order": per_topic_order[tp],
                },
            }
        )

    out_path.write_text(json.dumps(fixture_out, ensure_ascii=False, indent=2), encoding="utf-8")

    # Print summary
    print(f"Wrote: {out_path}")
    print(f"Subject pk={subject_pk} topics={len(topic_map)} tasks={len(merged)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
