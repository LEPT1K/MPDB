#!/usr/bin/env python3
"""Этап 1: Скачивание и парсинг исходных данных (без перевода и связей)"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from loader import DataLoader
from translator import Translator
from parsers.capec_parser import CAPECParser
from parsers.cwe_parser import CWEParser
from parsers.cve_parser import CVEParser
from parsers.attack_parser import ATTCKParser

def main():
    Config.ENABLE_TRANSLATION = False
    Config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    loader = DataLoader()
    translator = Translator(force_enable=False)  # без перевода

    # CAPEC
    print("\n🔹 CAPEC...")
    content = loader.fetch_with_retry(Config.SOURCES["capec"])
    if content:
        data = CAPECParser(translator).parse(content)
        with open(Config.OUTPUT_DIR / "capec_database.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ CAPEC: {len(data)} записей")

    # CWE
    print("\n🔹 CWE...")
    content = loader.fetch_zip_with_retry(Config.SOURCES["cwe"], target_extension=".xml")
    if content:
        data = CWEParser(translator).parse(content)
        with open(Config.OUTPUT_DIR / "cwe_database.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ CWE: {len(data)} записей")

    # CVE
    print("\n🔹 CVE...")
    cve_data = loader.fetch_gz_json(Config.SOURCES["cve_latest"])
    if cve_data:
        data = CVEParser(translator).parse(cve_data)
        with open(Config.OUTPUT_DIR / "cve_database.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ CVE: {len(data)} записей")

    # ATT&CK
    print("\n🔹 MITRE ATT&CK...")
    content = loader.fetch_with_retry(Config.SOURCES["attack_stix"])
    if content:
        data = ATTCKParser(translator).parse(content)
        with open(Config.OUTPUT_DIR / "mitre_attack.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ ATT&CK: {len(data)} записей")

    print("\n🎉 Этап 1 завершён. Файлы сохранены в output/")

if __name__ == "__main__":
    main()