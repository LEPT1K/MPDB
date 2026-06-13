#!/usr/bin/env python3
"""Этап 2: Обогащение перекрёстными ссылками и мерами защиты"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from cross_linker import CrossLinker

def main():
    print("\n🔗 Запуск связывания баз...")
    linker = CrossLinker(Config.OUTPUT_DIR)
    if not linker.load_databases():
        print("❌ Не удалось загрузить базы")
        return
    stats = linker.run()
    print(f"📊 Статистика обогащения: {stats}")
    linker.save_databases()
    print("✅ Этап 2 завершён. Связи заполнены.")

if __name__ == "__main__":
    main()