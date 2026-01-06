#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для проверки и исправления категорий тестов
Согласно структуре: ФОНЕТИКА, ҲОДИСАҲОИ ФОНЕТИКӢ ва ИМЛО
"""

import json
import re


def analyze_and_fix_categories():
    """
    Анализирует вопросы и правильно распределяет по категориям
    """
    
    # Правильные категории согласно PDF
    CORRECT_CATEGORIES = {
        "ФОНЕТИКА ва ҲОДИСАҲОИ ФОНЕТИКӢ": {
            "keywords": [
                "зада", "ҳиҷо", "садо", "ҳамсадо", "садонок", "ҳарф", 
                "овоз", "фонетик", "талаффуз", "ӣ-ро", "вазифа"
            ],
            "patterns": [
                r"зада.*ҳиҷо",
                r"ҳамсадо",
                r"садонок",
                r"вазифаи ҳарфи",
                r"овоз"
            ]
        },
        "ИМЛО": {
            "keywords": [
                "дуруст навишта", "имло", "нависӣ", "навиштан",
                "хато", "ғалат"
            ],
            "patterns": [
                r"дуруст.*навишта",
                r"калима.*навишта",
                r"имло"
            ]
        },
        "ЛЕКСИКА": {
            "keywords": [
                "маънӣ", "зидмаъно", "ҳаммаъно", "калима", "луғат",
                "истилоҳ", "термин", "синоним", "антоним"
            ],
            "patterns": [
                r"зидмаъно",
                r"ҳаммаъно",
                r"маънои.*калима"
            ]
        },
        "ФРАЗЕОЛОГИЯ": {
            "keywords": [
                "ибора", "зарбулмасал", "мақол", "таркиб", "фразеологӣ"
            ],
            "patterns": [
                r"ибора.*созед",
                r"зарбулмасал",
                r"таркиб"
            ]
        },
        "МОРФОЛОГИЯ": {
            "keywords": [
                "ҳиссаи нутқ", "исм", "феъл", "сифат", "зарф", "ҷонишин",
                "пешоянд", "пасванд", "калимасозӣ"
            ],
            "patterns": [
                r"ҳиссаи нутқ",
                r"исм.*феъл",
                r"пасванд",
                r"калима.*созед"
            ]
        },
        "СИНТАКСИС": {
            "keywords": [
                "ҷумла", "аъзо", "мубтадо", "хабар", "ҳол", "пуркунанда",
                "муайянкунанда", "мураккаб", "сода"
            ],
            "patterns": [
                r"аъзои ҷумла",
                r"мубтадо.*хабар",
                r"ҷумлаи.*мураккаб"
            ]
        },
        "АДАБИЁТ": {
            "keywords": [
                "адиб", "шоир", "асар", "китоб", "роман", "шеър", "байт",
                "Рӯдакӣ", "Фирдавсӣ", "Айнӣ", "Турсунзода"
            ],
            "patterns": [
                r"асари.*адиб",
                r"шоир",
                r"байт.*муайян"
            ]
        }
    }
    
    # Читаем тесты
    with open("test_database_clean.json", 'r', encoding='utf-8') as f:
        tests = json.load(f)
    
    print(f"📊 Всего тестов: {len(tests)}")
    print(f"\n🔍 Анализ текущих категорий:")
    
    # Анализ текущих категорий
    current_categories = {}
    for test in tests:
        cat = test['category']
        current_categories[cat] = current_categories.get(cat, 0) + 1
    
    for cat, count in sorted(current_categories.items()):
        print(f"   {cat}: {count}")
    
    # Функция определения категории
    def detect_category(question_text):
        question_lower = question_text.lower()
        
        # Проверяем по паттернам и ключевым словам
        scores = {}
        
        for category, rules in CORRECT_CATEGORIES.items():
            score = 0
            
            # Проверка паттернов
            for pattern in rules['patterns']:
                if re.search(pattern, question_text, re.IGNORECASE):
                    score += 3
            
            # Проверка ключевых слов
            for keyword in rules['keywords']:
                if keyword.lower() in question_lower:
                    score += 1
            
            if score > 0:
                scores[category] = score
        
        # Возвращаем категорию с максимальным счетом
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]
        
        return "ЛЕКСИКА"  # По умолчанию
    
    # Исправляем категории
    print(f"\n🔧 Исправление категорий...")
    
    changes = []
    for test in tests:
        old_category = test['category']
        new_category = detect_category(test['question_text'])
        
        if old_category != new_category:
            changes.append({
                'id': test['id'],
                'old': old_category,
                'new': new_category,
                'question': test['question_text'][:80]
            })
            test['category'] = new_category
    
    # Статистика изменений
    print(f"\n📊 Изменено категорий: {len(changes)}")
    
    if changes:
        print(f"\n📝 Примеры изменений (первые 10):")
        for change in changes[:10]:
            print(f"\n   ID {change['id']}:")
            print(f"   Было: {change['old']}")
            print(f"   Стало: {change['new']}")
            print(f"   Вопрос: {change['question']}...")
    
    # Новая статистика
    print(f"\n📊 Новое распределение по категориям:")
    new_categories = {}
    for test in tests:
        cat = test['category']
        new_categories[cat] = new_categories.get(cat, 0) + 1
    
    for cat, count in sorted(new_categories.items()):
        print(f"   {cat}: {count}")
    
    # Сохраняем исправленные данные
    with open("test_database_fixed.json", 'w', encoding='utf-8') as f:
        json.dump(tests, f, ensure_ascii=False, indent=4)
    
    print(f"\n✅ Сохранено в: test_database_fixed.json")
    
    # Сохраняем отчет об изменениях
    with open("category_changes_report.json", 'w', encoding='utf-8') as f:
        json.dump(changes, f, ensure_ascii=False, indent=2)
    
    print(f"📄 Отчет об изменениях: category_changes_report.json")
    
    return tests, changes


if __name__ == "__main__":
    tests, changes = analyze_and_fix_categories()
    print(f"\n🎉 Готово! Проверьте файл test_database_fixed.json")
