# 📰 Лента обновлений MITRE баз

Отслеживание актуальности локальных БД (CAPEC, CWE, CVE, MITRE ATT&CK) относительно официальных источников. Доступна на странице **"Главная"**.

## Возможности

- Статус каждой базы: 🟢 актуальна / 🟡 доступны обновления / 🔴 не распарсена
- Метаданные источника: размер, дата изменения
- Статистика локальной БД (количество записей)
- Кнопка "Проверить" — принудительный пересчёт (игнорирует кэш)
- Модальное окно "Детали" — подробная информация по источнику
- Прямые ссылки на официальные сайты (capec.mitre.org, cwe.mitre.org, attack.mitre.org, nvd.nist.gov)

## Архитектура

| Компонент | Файл | Назначение |
|---|---|---|
| Backend | `src/updates_checker.py` | Класс `UpdatesChecker` — проверка источников, кэш |
| API | `gui/app.py` | `/api/updates`, `/api/updates/<source_key>` |
| UI | `gui/templates/index.html` | Карточка ленты + модальное окно деталей |
| JS | `gui/static/js/app.js` | `loadUpdates`, `refreshUpdates`, `renderUpdates`, `showSourceDetails` |
| CSS | `gui/static/css/style.css` | Стили карточек обновлений |

## API

```
GET /api/updates              # список обновлений (из кэша, если свежий)
GET /api/updates?force=true   # принудительный пересчёт
GET /api/updates/<source_key> # детали источника: capec | cwe | attack | cve
```

Ответ `/api/updates`:
```json
{
  "updates": [
    {
      "source": "capec",
      "name": "CAPEC",
      "status": "up_to_date",        // up_to_date | outdated | missing
      "status_text": "Актуальна",
      "status_color": "success",     // success | warning | danger
      "url": "https://capec.mitre.org/",
      "local_stats": { "count": 615, "type": "list" },
      "metadata": { "content_length": "...", "last_modified": "...", "checked_at": "..." }
    }
  ],
  "last_checked": "1718070000",
  "sources_count": 4
}
```

## Кэширование

Результаты кэшируются на 1 час в `output/updates_cache.json` (`UpdatesChecker.CACHE_LIFETIME`). Удалите файл или нажмите "Проверить" для принудительного обновления.

## Источники

| База | Сайт | JSON для проверки |
|---|---|---|
| CAPEC | capec.mitre.org | raw.githubusercontent.com/mitre-attack/attack-website/.../capec.json |
| CWE | cwe.mitre.org | raw.githubusercontent.com/cwe/cwe-website/.../cwe.json |
| MITRE ATT&CK | attack.mitre.org | raw.githubusercontent.com/mitre/cti/.../enterprise-attack.json |
| CVE/NVD | nvd.nist.gov | services.nvld.nist.gov/rest/json/cves/2.0 |

## Диагностика

```bash
python tests/check_updates.py
```

Проверяет доступность всех источников, печатает статусы и сохраняет кэш. Сетевые ошибки для отдельных источников не считаются провалом — это нормально при ограниченном доступе.
