# -*- mode: python ; coding: utf-8 -*-
"""
Сборка MPDB в один .exe (папка dist/MPDB5/).

Исходники src/ и gui/ включаются как обычные файлы данных (не как
"замороженные" модули) — launcher.py добавляет их в sys.path во время
выполнения. Благодаря этому src/config.py остаётся редактируемым файлом
внутри сборки (страница "Настройки" в GUI пишет прямо в него).
"""

import os
from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
hiddenimports = []

for pkg in [
    'flask', 'flask_cors', 'flask_socketio', 'engineio', 'socketio',
    'simple_websocket', 'deep_translator', 'bs4', 'openpyxl',
    'reportlab', 'requests', 'werkzeug', 'jinja2',
]:
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hiddenimports += h

# gui/app.py и gui/exporters.py как обычные файлы данных рядом с шаблонами/статикой
datas += [
    ('gui/app.py', 'gui'),
    ('gui/exporters.py', 'gui'),
]

# Не даём PyInstaller "заморозить" код проекта в PYZ — он будет загружаться
# во время выполнения как обычные .py файлы из _internal/src и _internal/gui
excludes = [
    'config', 'loader', 'translator', 'normalizer', 'cross_linker',
    'ai_enricher', 'link_graph', 'updates_checker', 'menu', 'run_all', 'main',
    'step1_parse', 'step2_link', 'step3_enrich_ai', 'step4_autofill',
    'translate_fields', 'parsers', 'app', 'exporters',
]

a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MPDB5',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    Tree('src', prefix='src', excludes=['__pycache__', '*.pyc']),
    Tree('gui/templates', prefix=os.path.join('gui', 'templates')),
    Tree('gui/static', prefix=os.path.join('gui', 'static')),
    strip=False,
    upx=False,
    name='MPDB5',
)
