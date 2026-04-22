# llm-wiki-template

Шаблон для развёртывания LLM-wiki — структурированной персональной базы знаний, которую пишет и поддерживает Claude Code, а ты только направляешь ингест и задаёшь вопросы.

Основан на паттерне Karpathy ([llm-wiki.md](llm-wiki.md)) и заточен под Claude Code + Obsidian. Готовые слэш-команды `/ingest`, `/ingest-auto`, `/ingest-test`, `/wiki`, `/wiki-deep` + скрипты транскрипции (Whisper) и конвертации PDF (Docling).

## Что в шаблоне

```
├── llm-wiki.md              # исходная статья Karpathy про паттерн (идея)
├── CLAUDE.md                # инструкция Claude — как поддерживать wiki
├── .claude/
│   ├── commands/            # слэш-команды: /ingest, /ingest-auto, /ingest-test, /wiki, /wiki-deep
│   └── settings.json        # allow-list для bash-вызовов скриптов
├── tools/                   # локальные инструменты ingest
│   ├── extract_audio.sh     # любой контейнер → mp3 mono 128k 44.1kHz
│   ├── ingest_audio.sh      # audio/video → mp3 + транскрипт
│   ├── ingest_video.sh      # video → транскрипт одной командой
│   ├── transcribe.py        # Whisper API, авточанкинг под 25MB
│   ├── ingest_pdf.py        # PDF → markdown через Docling (локально, без API)
│   ├── validate_quotes.py   # защита от фабрикованных цитат/атрибуций
│   ├── requirements.txt
│   └── .env.example
└── vault/                   # Obsidian vault
    ├── .obsidian/           # минимальный конфиг (graph исключает raw/)
    ├── raw/                 # immutable источники (пусто, с .gitkeep)
    │   ├── lessons/
    │   ├── qna/
    │   ├── methodologies/
    │   ├── checklists/
    │   ├── articles/
    │   └── assets/
    └── wiki/                # тут пишет Claude
        ├── index.md         # каталог всех страниц
        ├── log.md           # хронология ingest/query/lint
        ├── conflicts.md     # расхождения между источниками
        └── sources/         # 1 страница на ingested источник
```

Тематические папки (`concepts/`, `conditions/`, `characters/`, `interventions/` и т.п.) **не созданы специально** — они появятся когда Claude увидит из материала, как именно ты хочешь резать эту тему. См. «Правило живой таксономии» в [CLAUDE.md](CLAUDE.md).

## Setup

### 1. Развернуть шаблон

```bash
git clone https://github.com/<ты>/llm-wiki-template my-wiki
cd my-wiki
rm -rf .git && git init   # свой репо, не привязанный к шаблону
```

### 2. Адаптировать `CLAUDE.md`

Открой `CLAUDE.md` и замени плейсхолдеры `{{ПРЕДМЕТ}}`, `{{ТИПЫ ИСТОЧНИКОВ}}`, `{{ЦЕЛЬ}}` в верхнем блоке на свою тему. Остальная структура — универсальная.

По умолчанию wiki на русском. Для другого языка:
- Замени «Правило №1» в `CLAUDE.md` на свой язык.
- В `tools/transcribe.py` смени `language="ru"` на нужный код (`en`, `es`, ...).
- Переведи stub-тексты в `vault/wiki/{index,log,conflicts}.md` и слэш-команды в `.claude/commands/` — или оставь (Claude разберётся, но язык инструкций влияет на язык результата).

### 3. Зависимости

```bash
# ffmpeg нужен для аудио/видео ingest
brew install ffmpeg          # macOS
# sudo apt install ffmpeg    # Linux

# Python зависимости (Whisper + Docling)
python3 -m venv tools/.venv
tools/.venv/bin/pip install -r tools/requirements.txt
```

Docling при первом запуске подкачает модели (~сотни MB). Если PDF-ingest не нужен — удали `docling` из `requirements.txt` перед установкой.

### 4. OpenAI API key

Whisper API нужен для транскрипции:

```bash
cp tools/.env.example tools/.env
# впиши sk-... в OPENAI_API_KEY
```

### 5. Obsidian

Открой `vault/` как vault в Obsidian. В графе ты увидишь только смысловую сетку — `raw/` скрыт фильтром в `vault/.obsidian/graph.json`.

Полезные плагины (не обязательные):
- **Obsidian Web Clipper** — браузер-экстеншн, клипает веб-статьи в markdown.
- **Dataview** — динамические таблицы по YAML frontmatter.
- **Marp** — markdown-слайды из wiki-контента.

## Использование

**Ingest одного файла** (интерактивно, с триажем и gate на таксономию):
```
/ingest
```
Claude покажет список новых файлов в `vault/raw/`, ты выберешь. Он прочитает источник, суммаризирует, создаст страницу-источник, обновит тематические страницы, индекс и лог.

ВАЖНО.
Сначала делаешь руками инжесты по основным ключевым файлам. Допустим это вебинар или записи основных уроков. Он создаест структуру графа по ним. Когда тут закончишь, можно переходить к авто загрузке остального.



**Batch ingest нескольких файлов** (параллельные subagents):
```
/ingest-auto sonnet
/ingest-auto opus
```
Аргумент обязателен — `sonnet` или `opus`. Оркестратор детектит новые raw-файлы, делает триаж, раздаёт работу subagent'ам, потом собирает результат.

**Тестовый ingest** — сравнить качество разных моделей на одном файле без записи в wiki:
```
/ingest-test vault/raw/<категория>/<файл>
```
Результат пишется в `vault/wiki/_ingest-tests/<slug>--<model>.md`.

**Query по графу**:
```
/wiki <вопрос>          # 1 хоп, для простых вопросов
/wiki-deep <вопрос>     # 2-3 хопа + sources + conflicts, для сложных
```
Отвечает **только** из wiki, без общих знаний. Если данных не хватает — честно скажет.

## Workflow на старте

1. Кинь первый источник в `vault/raw/<категория>/`.
2. `/ingest` → выбери его.
3. Claude сделает страницу-источник и (обычно) 1-3 тематические страницы. После ingest'а он спросит про таксономию, если есть смысл — соглашайся/предлагай альтернативу.
4. Повторяй с новыми источниками. К 3-5 источнику таксономия обычно устаканивается.
5. `/wiki <вопрос>` — начни задавать вопросы. Хорошие ответы можно предлагать зафайлить в wiki как новые страницы.
6. Периодически — «залинтуй wiki» (orphan-страницы, отсутствующие cross-references, пропущенные концепции).

## Тяжёлые источники (аудио/видео)

Стандарт: в `vault/raw/` живёт только перекодированный `mp3` (mono 128k 44.1kHz) + транскрипт `md`. Оригиналы удаляются после ingest'а.

```bash
tools/ingest_audio.sh vault/raw/qna/efir-2024-03.m4a vault/raw/qna/efir-2024-03
# → vault/raw/qna/efir-2024-03.mp3
# → vault/raw/qna/efir-2024-03.md
# скрипт печатает команду для удаления оригинала в конце
```

## Валидация цитат

`/ingest` включает обязательный gate на `validate_quotes.py` — он проверяет что все `> blockquote` в странице-источнике реально есть в raw-транскрипте, и ловит сфабрикованные атрибуции (`стр. N`, таймкоды), когда их в raw нет.

Запустить вручную:
```bash
python3 tools/validate_quotes.py vault/wiki/sources/<slug>.md vault/raw/<путь>/<файл>.md
```

## Лицензия

MIT (или на твой вкус — добавь `LICENSE` до первого коммита).

## Кредиты

- Паттерн LLM-wiki — [Andrej Karpathy](https://github.com/karpathy) (см. [llm-wiki.md](llm-wiki.md)).
- Транскрипция — [OpenAI Whisper](https://platform.openai.com/docs/guides/speech-to-text).
- PDF → markdown — [Docling](https://github.com/DS4SD/docling).
- Граф, бэклинки, vault — [Obsidian](https://obsidian.md/).
