import subprocess
import sys
from pathlib import Path

# Важно: перевод идёт ДО автозаполнения — автозаполнение работает по русским
# словарям/шаблонам и должно дописывать уже переведённую базу.
scripts = ["step1_parse.py", "step2_link.py", "translate_fields.py", "step4_autofill.py"]

for script in scripts:
    print(f"\n🚀 Выполнение {script}...")
    result = subprocess.run([sys.executable, str(Path(__file__).parent / script)])
    if result.returncode != 0:
        print(f"❌ Ошибка в {script}")
        break