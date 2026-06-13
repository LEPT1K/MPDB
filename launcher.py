#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Единая точка входа для MPDB (MITRE Parser Databases).

В обычном режиме (python launcher.py) запускает GUI и открывает браузер.

В собранном .exe этот же файл служит и точкой запуска GUI, и "обёрткой"
для шагов парсера: gui/app.py запускает их как
    <exe> -u <путь_к_скрипту.py>
В .exe нет отдельного python.exe, поэтому при таком вызове launcher
выполняет указанный скрипт внутри себя через runpy, не поднимая GUI.
"""

import sys
import threading
import time
import webbrowser
from pathlib import Path


def is_frozen():
    return getattr(sys, 'frozen', False)


def get_data_dir():
    """Каталог с исходниками src/ и gui/ (только для чтения модулей)."""
    if is_frozen():
        return Path(sys._MEIPASS)
    return Path(__file__).parent


def run_step_script(script_path: str):
    """Выполнить src/stepN_*.py внутри собранного .exe (замена python -u script.py)."""
    import runpy
    sys.argv = [script_path] + sys.argv[3:]
    sys.path.insert(0, str(Path(script_path).parent))
    runpy.run_path(script_path, run_name='__main__')


def run_gui():
    data_dir = get_data_dir()
    sys.path.insert(0, str(data_dir / 'src'))
    sys.path.insert(0, str(data_dir / 'gui'))

    from app import socketio, app

    print("=" * 50)
    print("  MPDB (MITRE Parser Databases) - Графический интерфейс")
    print("=" * 50)
    print()
    print("Для остановки нажмите Ctrl+C")
    print()

    ports = [5000, 5001]
    for port in ports:
        try:
            print("Откройте браузер и перейдите по адресу:")
            print(f"   http://localhost:{port}")
            print()

            def open_browser(p=port):
                time.sleep(1.5)
                webbrowser.open(f"http://localhost:{p}")

            threading.Thread(target=open_browser, daemon=True).start()

            socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)
            break
        except OSError as e:
            if hasattr(e, 'winerror') and e.winerror == 10048:  # Порт занят
                if port == ports[-1]:
                    print("\nНе удалось запустить сервер. Порты 5000 и 5001 заняты.")
                    sys.exit(1)
                print(f"Порт {port} занят. Пробуем следующий порт...")
            else:
                raise


def main():
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')

    # Переинвокация для шагов парсера: <exe> -u <script.py> [...]
    if is_frozen() and len(sys.argv) >= 3 and sys.argv[1] == '-u' and sys.argv[2].endswith('.py'):
        run_step_script(sys.argv[2])
        return

    run_gui()


if __name__ == '__main__':
    main()
