# src/translator.py
import re
import time
import json
import ssl
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from deep_translator import GoogleTranslator
from config import Config

# Создаём безопасный SSL-контекст для обхода ошибок SSL EOF
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

class Translator:
    """Онлайн-переводчик через Google Translate с дедупликацией, многопоточностью и кэшированием"""

    MAX_TEXT_LENGTH = 4500  # безопасный лимит для Google Translate
    CACHE_SAVE_EVERY = 200  # сохранять кэш на диск каждые N новых переводов

    def __init__(self, target_lang: str = None, force_enable: bool = False,
                 workers: int = None, delay: float = None):
        self.enabled = force_enable or Config.ENABLE_TRANSLATION
        self.target_lang = target_lang or Config.TRANSLATE_TO
        self.delay = delay if delay is not None else getattr(Config, 'TRANSLATION_DELAY', 0.4)
        self.max_retries = getattr(Config, 'TRANSLATION_MAX_RETRIES', 5)
        self.workers = max(1, int(workers if workers is not None else getattr(Config, 'TRANSLATION_WORKERS', 5)))

        if self.enabled:
            try:
                GoogleTranslator(source='auto', target=self.target_lang)
                self._executor = ThreadPoolExecutor(max_workers=self.workers)
                print(f"🌐 Онлайн-переводчик готов (Google Translate → {self.target_lang}, потоков: {self.workers})")
            except Exception as e:
                print(f"⚠️ Ошибка инициализации переводчика: {e}")
                self.enabled = False
                self._executor = None
        else:
            self._executor = None
            print("⚡ Перевод отключён в настройках")

        self._cache = {}
        self._cache_lock = threading.Lock()
        self._cache_file = Config.OUTPUT_DIR / "translate_cache.json"
        self._load_cache()
        self._dirty = 0

    def _load_cache(self):
        if self._cache_file.exists():
            try:
                with open(self._cache_file, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
                print(f"📦 Загружено {len(self._cache)} переводов из кэша")
            except:
                pass

    def _save_cache(self):
        try:
            self._cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._cache_file, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, ensure_ascii=False, indent=2)
        except:
            pass

    def _split_long_text(self, text: str) -> list:
        """Разбивает длинный текст на части по предложениям или абзацам, не превышая MAX_TEXT_LENGTH"""
        if len(text) <= self.MAX_TEXT_LENGTH:
            return [text]

        parts = text.split('\n\n')
        result = []
        for part in parts:
            if len(part) <= self.MAX_TEXT_LENGTH:
                result.append(part)
            else:
                subparts = re.split(r'(?<=[.!?])\s+', part)
                current = ""
                for sub in subparts:
                    if len(current) + len(sub) + 1 <= self.MAX_TEXT_LENGTH:
                        current = (current + " " + sub).strip() if current else sub
                    else:
                        if current:
                            result.append(current)
                        current = sub
                if current:
                    result.append(current)
        return result

    def _is_russian(self, text: str) -> bool:
        return bool(re.search(r'[а-яА-ЯёЁ]', text))

    def _is_skippable(self, text: str) -> bool:
        if not text or not isinstance(text, str):
            return True
        if not text.strip():
            return True
        if re.match(r'^(CAPEC|CWE|CVE|T\d{4}(\.\d{3})?|[A-Z]{2,}-\d+)$', text.strip()):
            return True
        if self._is_russian(text):
            return True
        return False

    def _translate_part(self, part: str) -> str:
        """Переводит один фрагмент текста (выполняется в отдельном потоке)"""
        translator = GoogleTranslator(source='auto', target=self.target_lang)
        for attempt in range(self.max_retries):
            try:
                if self.delay > 0:
                    time.sleep(self.delay)
                result = translator.translate(part)
                return result if result else part
            except Exception as e:
                print(f"⚠️ Попытка {attempt+1}/{self.max_retries} для '{part[:40]}...' провалена: {e}")
                time.sleep(2 * (attempt + 1))
        return part

    def _translate_parts_concurrently(self, parts: list):
        """Переводит уникальные фрагменты параллельно и складывает результаты в кэш"""
        total = len(parts)
        print(f"    🌐 Перевод {total} уникальных фрагментов ({self.workers} потоков, задержка {self.delay}с)...")
        completed = 0
        futures = {self._executor.submit(self._translate_part, part): part for part in parts}
        for future in as_completed(futures):
            part = futures[future]
            try:
                translated = future.result()
            except Exception:
                translated = part
            with self._cache_lock:
                self._cache[part] = translated
                self._dirty += 1
                if self._dirty >= self.CACHE_SAVE_EVERY:
                    self._save_cache()
                    self._dirty = 0
            completed += 1
            if completed % 50 == 0 or completed == total:
                print(f"      ...переведено {completed}/{total}")

    def translate_batch(self, texts: list) -> list:
        """Переводит список строк с глобальной дедупликацией и параллельными запросами"""
        if not self.enabled:
            return texts[:] if texts else []
        if not texts:
            return []

        results = list(texts)
        pending_parts = {}   # part -> None, сохраняет порядок появления
        item_plan = {}       # index -> (cache_key, [parts])

        for i, text in enumerate(texts):
            if self._is_skippable(text):
                continue
            stripped = text.strip()
            if stripped in self._cache:
                results[i] = self._cache[stripped]
                continue

            norm = stripped.replace('_', ' ').strip() if '_' in stripped else stripped
            parts = self._split_long_text(norm)
            item_plan[i] = (stripped, parts)
            for part in parts:
                if part not in self._cache:
                    pending_parts.setdefault(part, None)

        if not item_plan:
            return results

        if pending_parts:
            self._translate_parts_concurrently(list(pending_parts.keys()))

        for i, (cache_key, parts) in item_plan.items():
            translated_parts = [self._cache.get(p, p) for p in parts]
            full = " ".join(translated_parts)
            results[i] = full
            self._cache[cache_key] = full

        self._save_cache()
        self._dirty = 0
        return results

    def translate(self, text: str, use_cache: bool = True) -> str:
        if not self.enabled or not text or not isinstance(text, str):
            return text
        result = self.translate_batch([text])
        return result[0] if result else text

    def translate_list(self, items: list) -> list:
        return self.translate_batch(items)

    def __del__(self):
        if hasattr(self, '_cache'):
            self._save_cache()
        if getattr(self, '_executor', None):
            self._executor.shutdown(wait=False)
