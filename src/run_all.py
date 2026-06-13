import subprocess
import sys
from pathlib import Path

scripts = ["step1_parse.py", "step2_link.py", "step4_autofill.py", "translate_fields.py"]

for script in scripts:
    print(f"\n🚀 Выполнение {script}...")
    result = subprocess.run([sys.executable, str(Path(__file__).parent / script)])
    if result.returncode != 0:
        print(f"❌ Ошибка в {script}")
        break