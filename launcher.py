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

import socket
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


def _port_is_free(port: int) -> bool:
    """Проверяет, свободен ли порт на localhost (пробное связывание)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(('127.0.0.1', port))
        return True
    except OSError:
        return False
    finally:
        s.close()


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

    # Выбираем свободный порт ДО старта сервера, чтобы не открывать браузер
    # на занятый порт (иначе всплывала мёртвая вкладка localhost:5000).
    chosen = next((p for p in (5000, 5001) if _port_is_free(p)), None)
    if chosen is None:
        print("\nНе удалось запустить сервер. Порты 5000 и 5001 заняты.")
        sys.exit(1)

    print("Откройте браузер и перейдите по адресу:")
    print(f"   http://localhost:{chosen}")
    print()

    def open_browser(p=chosen):
        time.sleep(1.5)
        webbrowser.open(f"http://localhost:{p}")

    threading.Thread(target=open_browser, daemon=True).start()

    # host=127.0.0.1: локальный инструмент не должен слушать на всех интерфейсах LAN
    socketio.run(app, host='127.0.0.1', port=chosen, debug=False, allow_unsafe_werkzeug=True)


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
