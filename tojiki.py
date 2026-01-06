import pdfplumber
import re
import json

def parse_tj_test(pdf_path, output_json):
    questions = []
    current_category = "Умумӣ"
    
    # Регулярные выражения для вариантов (поддержка кириллицы и латиницы)
    re_question_start = re.compile(r'^(\d+)\s+(.+)') # Начало вопроса: "1 Текст..."
    re_option = re.compile(r'^([АВСДABCDабвгдabcd])\)\s*(.*)', re.IGNORECASE)    # Варианты: "А) текст" или "A) текст"
    re_matching = re.compile(r'^(\d)\)\s+(.*)')      # Для Part B: "1) текст"

    with pdfplumber.open(pdf_path) as pdf:
        temp_q = None
        
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue

            lines = text.split('\n')
            for line in lines:
                line = line.strip()
                if not line: continue

                # 1. Определение категории (обычно заглавные буквы в отдельной строке)
                if line.isupper() and len(line) > 15 and not re_option.match(line):
                    current_category = line
                    continue

                # 2. Начало нового вопроса
                q_match = re_question_start.match(line)
                if q_match:
                    if temp_q:
                        questions.append(temp_q)
                    
                    temp_q = {
                        "id": int(q_match.group(1)),
                        "category": current_category,
                        "question_text": q_match.group(2),
                        "options": {},
                        "matching_options": {}, # Для заданий типа Part B
                        "is_poetry": False
                    }
                    continue

                # 3. Парсинг вариантов A, B, C, D (кириллица и латиница)
                o_match = re_option.match(line)
                if o_match and temp_q:
                    option_letter = o_match.group(1).upper()
                    # Конвертируем кириллицу в латиницу для единообразия
                    cyrillic_to_latin = {'А': 'A', 'В': 'B', 'С': 'C', 'Д': 'D'}
                    option_letter = cyrillic_to_latin.get(option_letter, option_letter)
                    
                    option_text = o_match.group(2).strip()
                    if option_text:  # Добавляем только если есть текст
                        temp_q["options"][option_letter] = option_text
                    continue

                # 4. Парсинг цифровых вариантов (1, 2, 3...) для заданий на соответствие
                m_match = re_matching.match(line)
                if m_match and temp_q:
                    temp_q["matching_options"][m_match.group(1)] = m_match.group(2)
                    continue

                # 5. Если это не вопрос и не вариант — это продолжение текста
                if temp_q and not re_option.match(line):
                    # Добавляем только если это не мусор (не содержит много спецсимволов)
                    if len(re.findall(r'[а-яА-ЯёЁӣӢҳҲқҚғҒҷҶ]', line)) > len(line) * 0.3:
                        temp_q["question_text"] += "\n" + line
                        temp_q["is_poetry"] = True

        # Добавляем последний вопрос
        if temp_q:
            questions.append(temp_q)

    # Сохранение в файл
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(questions, f, ensure_ascii=False, indent=4)

    print(f"Парсинг завершен. Собрано вопросов: {len(questions)}")

# Запуск скрипта
if __name__ == "__main__":
    parse_tj_test("Забони точики Кластери 1.pdf", "test_database.json")