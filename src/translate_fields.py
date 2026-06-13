#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для выборочного перевода полей в JSON-файлах MPDB.
Использует онлайн-переводчик (Google Translate) для быстрой работы.
Запускать после генерации английских JSON.
"""
import json
from pathlib import Path
from config import Config
from translator import Translator

# Поля, которые нужно перевести в каждом типе файла
FIELDS_TO_TRANSLATE = {
    "capec_database.json": ["name", "description", "severity", "prerequisites", "mitigations"],
    "cwe_database.json": ["name", "description", "mitigation", "category", "detection_methods"],
    "cve_database.json": ["description", "severity", "mitigations", "affected_software", "attack_type", "requires_service"],
    "mitre_attack.json": ["name", "description", "requires_service", "mitigations", "detection", "tactic"]
}

def collect_texts(data: list, fields: list):
    """Собирает все строки для перевода вместе с указателями для обратной записи"""
    texts = []
    pointers = []  # (item_idx, field, list_idx или None)
    for idx, item in enumerate(data):
        for field in fields:
            if field not in item:
                continue
            value = item[field]
            if isinstance(value, str):
                texts.append(value)
                pointers.append((idx, field, None))
            elif isinstance(value, list):
                for li, sub in enumerate(value):
                    if isinstance(sub, str):
                        texts.append(sub)
                        pointers.append((idx, field, li))
    return texts, pointers

def apply_translations(data: list, pointers: list, originals: list, translated: list) -> int:
    """Записывает переведённые строки обратно в данные, возвращает число изменённых элементов"""
    updated_items = set()
    for (idx, field, li), original, new_value in zip(pointers, originals, translated):
        if new_value == original:
            continue
        if li is None:
            data[idx][field] = new_value
        else:
            data[idx][field][li] = new_value
        updated_items.add(idx)
    return len(updated_items)

def translate_file(filepath: Path, fields: list, translator: Translator):
    print(f"📄 Обработка {filepath.name}...")
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    texts, pointers = collect_texts(data, fields)
    unique_count = len(set(t.strip() for t in texts if isinstance(t, str) and t.strip()))
    print(f"  🔎 Найдено {len(texts)} строк ({unique_count} уникальных) для перевода")

    translated = translator.translate_batch(texts)
    updated = apply_translations(data, pointers, texts, translated)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ {filepath.name}: переведено элементов — {updated} из {len(data)}")

def main():
    print("🎯 Выборочный перевод полей JSON-файлов (онлайн-режим)")
    translator = Translator(force_enable=True)   # принудительное включение перевода
    if not translator.enabled:
        print("❌ Не удалось включить переводчик")
        return

    output_dir = Config.OUTPUT_DIR
    for filename, fields in FIELDS_TO_TRANSLATE.items():
        filepath = output_dir / filename
        if filepath.exists():
            translate_file(filepath, fields, translator)
        else:
            print(f"⚠️ Файл {filename} не найден, пропущен")

    translator._save_cache()
    print("🎉 Готово! Все указанные поля переведены.")

if __name__ == "__main__":
    main()
