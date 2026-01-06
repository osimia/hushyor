import pdfplumber
import re
import json

def parse_answer_keys(pdf_path, output_json, max_page=6):
    """
    Парсит ключи ответов из PDF файла
    Структура: номер вопроса -> правильный ответ (A, B, C, D)
    """
    answer_keys = {}
    
    with pdfplumber.open(pdf_path) as pdf:
        # Читаем только до указанной страницы
        pages_to_read = min(max_page, len(pdf.pages))
        
        for page_num in range(pages_to_read):
            page = pdf.pages[page_num]
            text = page.extract_text()
            
            if not text:
                continue
            
            print(f"\n=== Страница {page_num + 1} ===")
            print(text[:500])  # Показываем первые 500 символов для анализа
            
            lines = text.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Ищем все пары "номер буква" в строке (таблица с несколькими колонками)
                # Паттерн: число (1-3 цифры) + пробелы + буква (A/B/C/D или А/В/С/Д)
                matches = re.findall(r'(\d{1,3})\s+([АВСДABCDабвгдabcd])\b', line, re.IGNORECASE)
                
                for match in matches:
                    question_num = int(match[0])
                    answer = match[1].upper()
                    
                    # Конвертируем кириллицу в латиницу
                    cyrillic_to_latin = {'А': 'A', 'В': 'B', 'С': 'C', 'Д': 'D'}
                    answer = cyrillic_to_latin.get(answer, answer)
                    
                    # Проверяем, что это валидный ответ и разумный номер вопроса
                    if answer in ['A', 'B', 'C', 'D'] and 1 <= question_num <= 1000:
                        answer_keys[question_num] = answer
                        print(f"Найден ключ: {question_num} -> {answer}")
    
    # Сохраняем в JSON
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(answer_keys, f, ensure_ascii=False, indent=4, sort_keys=True)
    
    print(f"\n✅ Парсинг завершен!")
    print(f"Всего ключей найдено: {len(answer_keys)}")
    print(f"Сохранено в: {output_json}")
    
    # Показываем первые 10 ключей
    print("\nПервые 10 ключей:")
    for i in range(1, min(11, len(answer_keys) + 1)):
        if i in answer_keys:
            print(f"  {i}: {answer_keys[i]}")

if __name__ == "__main__":
    parse_answer_keys(
        "Забони точики Кластери 1 key.pdf",
        "answer_keys.json",
        max_page=8  # Парсим только до 8 страницы включительно
    )
