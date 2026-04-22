# Log

Хронология работы с wiki: ingest, query, lint. Append-only.

Формат заголовков фиксирован для grep'абельности:

```
## [YYYY-MM-DD] ingest | <название источника>
## [YYYY-MM-DD] query | <короткое описание вопроса>
## [YYYY-MM-DD] lint
```

Быстрая выжимка последних записей:

```bash
grep "^## \[" vault/wiki/log.md | tail -10
```

---

<!-- Первая запись появится после первого ingest'а. См. CLAUDE.md → «Формат log.md». -->
