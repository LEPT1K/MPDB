# src/menu.py
import subprocess
import sys
import re
import json
from pathlib import Path
from config import Config

def update_config_file(service, api_key=None):
    """Обновляет параметры TRANSLATION_SERVICE и YANDEX_API_KEY в config.py"""
    config_path = Path(__file__).parent / 'config.py'
    with open(config_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Замена TRANSLATION_SERVICE
    content = re.sub(
        r'^(TRANSLATION_SERVICE\s*=\s*).*',
        f'\\g<1>"{service}"',
        content,
        flags=re.MULTILINE
    )

    # Замена YANDEX_API_KEY
    if api_key:
        content = re.sub(
            r'^(YANDEX_API_KEY\s*=\s*).*',
            f'\\g<1>"{api_key}"',
            content,
            flags=re.MULTILINE
        )

    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(content)

    # Перезагружаем Config
    import importlib
    import config
    importlib.reload(config)
    from config import Config
    globals()['Config'] = Config

def update_translation_params(workers, delay, max_retries):
    """Обновляет параметры перевода в config.py"""
    config_path = Path(__file__).parent / 'config.py'
    with open(config_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Замена TRANSLATION_WORKERS
    content = re.sub(
        r'^(TRANSLATION_WORKERS\s*=\s*).*',
        f'\\g<1>{workers}',
        content,
        flags=re.MULTILINE
    )
    # Замена TRANSLATION_DELAY
    content = re.sub(
        r'^(TRANSLATION_DELAY\s*=\s*).*',
        f'\\g<1>{delay}',
        content,
        flags=re.MULTILINE
    )
    # Замена TRANSLATION_MAX_RETRIES
    content = re.sub(
        r'^(TRANSLATION_MAX_RETRIES\s*=\s*).*',
        f'\\g<1>{max_retries}',
        content,
        flags=re.MULTILINE
    )

    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(content)

    # Перезагружаем Config
    import importlib
    import config
    importlib.reload(config)
    from config import Config
    globals()['Config'] = Config

def configure_translation():
    """Интерактивная настройка сервиса перевода"""
    print("\n--- Настройка перевода ---")
    print("Доступные сервисы:")
    print("  google - Google Translate (бесплатно, без ключа, ограничения по длине текста)")
    print("  yandex - Яндекс.Переводчик (требуется API-ключ, стабильнее)")
    service = input("Выберите сервис (google/yandex): ").strip().lower()
    if service not in ['google', 'yandex']:
        print("Неверный ввод. Настройка не изменена.")
        return

    api_key = None
    if service == 'yandex':
        api_key = input("Введите API-ключ Яндекса: ").strip()
        if not api_key:
            print("Ключ не может быть пустым. Настройка не изменена.")
            return
        print("Ключ сохранён.")
    else:
        print("Для Google ключ не требуется.")

    update_config_file(service, api_key)
    print(f"Сервис перевода установлен: {service}")
    if api_key:
        print("API-ключ Яндекса обновлён.")

def configure_translation_params():
    """Интерактивная настройка параметров перевода (потоки, задержка, повторы)"""
    print("\n--- Настройка параметров перевода ---")
    print(f"Текущие значения: workers={Config.TRANSLATION_WORKERS}, delay={Config.TRANSLATION_DELAY}, max_retries={Config.TRANSLATION_MAX_RETRIES}")
    try:
        workers = int(input("Число параллельных потоков перевода (напр. 5): ").strip())
        delay = float(input("Задержка перед запросом в потоке, в секундах (напр. 0.4): ").strip())
        max_retries = int(input("Число повторных попыток при ошибке (напр. 5): ").strip())
    except ValueError:
        print("Ошибка ввода. Параметры не изменены.")
        return

    update_translation_params(workers, delay, max_retries)
    print("Параметры перевода обновлены и сохранены в config.py")

def run_script(script_name, extra_args=None):
    script_path = Path(__file__).parent / script_name
    cmd = [sys.executable, str(script_path)]
    if extra_args:
        cmd.extend(extra_args)
    subprocess.run(cmd, cwd=str(Path(__file__).parent.parent))

def clear_translation_cache():
    cache_file = Config.OUTPUT_DIR / "translate_cache.json"
    if cache_file.exists():
        cache_file.unlink()
        print("🧹 Кэш перевода удалён.")
    else:
        print("📭 Кэш перевода не найден.")

def clear_bad_translations():
    """Удаляет из кэша записи, где перевод явно некачественный"""
    cache_file = Config.OUTPUT_DIR / "translate_cache.json"
    if not cache_file.exists():
        print("📭 Кэш перевода не найден.")
        return

    with open(cache_file, "r", encoding="utf-8") as f:
        cache = json.load(f)

    removed = 0
    keys_to_remove = []
    for orig, trans in cache.items():
        if trans.count('_') > 2 or trans == orig or len(trans.strip()) < 2:
            keys_to_remove.append(orig)

    for key in keys_to_remove:
        del cache[key]
        removed += 1

    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

    print(f"🧹 Удалено {removed} некачественных переводов из кэша.")

def main():
    while True:
        service = Config.TRANSLATION_SERVICE
        print("\n" + "="*40)
        print("   MPDB (MITRE Parser Databases) - МЕНЮ")
        print("="*40)
        print(f"1. Скачать и распарсить базы (без перевода)")
        print(f"2. Связать данные (заполнить перекрёстные ссылки)")
        print(f"3. Автозаполнение пустых полей (связи/факты/STIX/шаблоны)")
        print(f"4. AI-обогащение (заполнить пустые поля)")
        print(f"5. Перевести выбранные поля (текущий сервис: {service})")
        print(f"6. Запустить все этапы последовательно")
        print(f"7. Выбрать сервис перевода")
        print(f"8. Очистить кэш перевода")
        print(f"9. Очистить некачественные переводы из кэша")
        print(f"10. Настроить параметры перевода")
        print(f"0. Выход")
        choice = input("Ваш выбор: ").strip()

        if choice == "1":
            run_script("step1_parse.py")
        elif choice == "2":
            run_script("step2_link.py")
        elif choice == "3":
            run_script("step4_autofill.py")
        elif choice == "4":
            run_script("step3_enrich_ai.py")
        elif choice == "5":
            extra = []
            if service == 'yandex' and Config.YANDEX_API_KEY:
                extra = ["--service", service, "--api-key", Config.YANDEX_API_KEY]
            elif service == 'yandex' and not Config.YANDEX_API_KEY:
                print("⚠️ Для Яндекса требуется API-ключ. Настройте сервис (пункт 7).")
                continue
            else:
                extra = ["--service", service]
            run_script("translate_fields.py", extra_args=extra)
        elif choice == "6":
            print("Запуск всех этапов...")
            run_script("step1_parse.py")
            run_script("step2_link.py")
            run_script("step4_autofill.py")
            run_script("step3_enrich_ai.py")
            extra = []
            if service == 'yandex' and Config.YANDEX_API_KEY:
                extra = ["--service", service, "--api-key", Config.YANDEX_API_KEY]
            elif service == 'yandex' and not Config.YANDEX_API_KEY:
                print("⚠️ Для Яндекса требуется API-ключ. Пропускаем перевод.")
            else:
                extra = ["--service", service]
            if extra or service == 'google':
                run_script("translate_fields.py", extra_args=extra)
        elif choice == "7":
            configure_translation()
        elif choice == "8":
            clear_translation_cache()
        elif choice == "9":
            clear_bad_translations()
        elif choice == "10":
            configure_translation_params()
        elif choice == "0":
            print("Выход.")
            break
        else:
            print("Неверный ввод, попробуйте снова.")

if __name__ == "__main__":
    main()