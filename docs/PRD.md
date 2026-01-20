---
title: "PRD: skillregistry (trusted) + project-bootstrap skill v0.1"
status: draft
---

# PRD: skillregistry (trusted) + project-bootstrap skill v0.1

**Статус:** Draft / v0.1
**Цель:** создать “trusted” репозиторий навыков `skillregistry` и bootstrap skill, который инициализирует проект (Codex, Claude позже) установкой нужных skills из доверенного банка и генерацией проектных overlay‑skills без поломки кастомизаций.

---

## 1) Контекст и проблема

Мы хотим AI‑поток разработки, где:
- навыки (Skills) живут вне контекста и подгружаются по необходимости;
- проект на старте получает правильный фундамент: базовые skills + проектные “overlay” skills;
- новые проекты быстро запускаются, а навыки обновляются удобно и безопасно.

**Проблема:**
- наивная “память” через контекст шумит и ухудшает качество;
- навыки нужно ставить **только из нашего проверенного банка**, не из внешних каталогов;
- нельзя делать “универсальный установщик”, который не использует сильные стороны Codex/Claude — используем стандартные механизмы (директории skills и git), а различия платформ учитываем позже (plugins/hooks/subagents — отдельным шагом).

---

## 2) Что мы строим (MVP v0.1)

### 2.1. Trusted repository: `skillregistry`
Новый git‑репозиторий (стартуем с нуля), который содержит:
- `skills/<skill_name>/SKILL.md` — reusable skills (банк)
- `templates/*` — шаблоны для генерации project overlay skills
- `catalog/skillsets.json` — базовые “skillsets” для выбора навыков по детекту проекта
- `skills/project-bootstrap/*` — bootstrap skill + скрипт, который:
  - клонирует registry в проект (в `.agent/skillregistry`)
  - детектит стек проекта
  - выбирает нужные registry skills
  - устанавливает их в `.codex/skills` (Claude пока пропускается)
  - генерирует overlay‑skills (`<prefix>-project-workflow`, `<prefix>-api-*`) безопасно (не затирая ручные правки)

### 2.2. Bootstrap skill (project-bootstrap)
**Один стартовый skill**, который запускается в проекте и “поднимает” всё остальное.

---

## 3) Основные сценарии использования

1) **Новый проект**
Запускаем bootstrap → получаем набор skills под стек + проектный workflow skill + скелеты API skills.

2) **Проект изменился (например, добавили Rust рядом с Go)**
Перезапускаем bootstrap → устанавливается новый набор registry skills, **старые лишние удаляются**, overlays обновляются безопасно.

3) **Обновление registry (новые версии skills)**
Меняем `SKILLREGISTRY_REF` и перезапускаем bootstrap → registry skills обновляются, overlays не ломаются.

---

## 4) Термины

- **registry skills** — навыки из `skillregistry/skills/*`, считаются read-only (в проекте не редактируем напрямую).
- **overlay skills** — проектные навыки, генерируемые bootstrap’ом (например `<prefix>-project-workflow`, `<prefix>-api-<name>`). Их можно редактировать вручную; bootstrap **не должен** ломать эти кастомизации.
- **targets** — `codex` и `claude` (установка в `.codex/skills`, Claude пока пропускается и фиксируется в TODO/state).

---

## 5) Требования (Functional)

### 5.1. Инициализация registry в проекте
Bootstrap должен:
- создавать/обновлять локальный клон registry в проекте:
  `.agent/skillregistry`
- принимать:
  - `SKILLREGISTRY_GIT` (git URL или локальный путь)
  - `SKILLREGISTRY_REF` (branch/tag/commit; default: `main`)
- записывать фактически используемый commit hash в state.

### 5.2. Детект проекта
Bootstrap должен (MVP эвристики):
- определить языки по файлам:
  - Go: `go.mod`
  - Rust: `Cargo.toml`
  - Python: `pyproject.toml` или `requirements.txt`
  - TS/JS: `package.json`
- определить наличие CI: `.github/workflows/`
- определить Docker: `Dockerfile`, `docker-compose.yml`, `compose.yaml`
- обнаружить внешние API (эвристика v0.1):
  - парсить `.env.example`, `.env`, `env.example` на шаблоны `PREFIX_API_KEY`, `PREFIX_TOKEN`, `PREFIX_BASE_URL`, `PREFIX_API_URL`
  - `PREFIX` нормализовать в lowercase, недопустимые символы заменить `_`

### 5.3. Выбор skillset
В registry должен быть файл:
- `catalog/skillsets.json`

Пример (MVP):
```json
{
  "baseline": ["tdd-loop", "code-review", "api-openapi-generic"],
  "lang_go": ["lang-go"],
  "lang_rust": ["lang-rust"],
  "lang_python": ["lang-python"],
  "lang_ts": ["lang-ts"]
}
```

Bootstrap должен:

- взять `baseline`
- добавить языковые skills на основе детекта
- убрать дубликаты, сохраняя порядок

### 5.4. Установка registry skills в проект

Для каждого выбранного registry skill:

- источник: `.agent/skillregistry/skills/<name>`
- destination:
  - `.codex/skills/<name>` (Claude пока пропускается)
- метод установки:
  - `--install-method skill-installer` (default): системный skill-installer, не перезаписывает существующие директории без `--force-overwrite-registry-skills`
  - `--install-method local`: локальная копия из `.agent/skillregistry` (для тестов/офлайна)

### 5.5. Чистка устаревших registry skills

Если набор registry skills изменился при повторном запуске bootstrap:

- необходимо удалить те skills, которые были установлены bootstrap’ом ранее, но теперь не требуются.
- удалять **только** то, что указано в предыдущем `.agent/skills_state.json` как `registry_skills_installed`, и отсутствует в новом списке.
- не удалять overlay skills и не удалять неизвестные папки (вне state).

### 5.6. Генерация overlay skills (обязательные)

Bootstrap должен создать/обеспечить overlay skills:

- `<prefix>-project-workflow` (обязателен всегда)
- `<prefix>-api-<name>` для каждого обнаруженного API (если есть)

Префикс:
- по умолчанию берётся из имени корня проекта (slug, 3–4 символа)
- можно переопределить через `--project-prefix`

Если найден похожий overlay (например `project-workflow`, `*-project-workflow`, `api-foo`, `*-api-foo`), то создание пропускается, **если** не указан `--force-create-overlays` и префикс не был изменён.
При смене префикса bootstrap не переименовывает старые overlays, а создаёт новые и оставляет TODO для ручной миграции.

Overlay располагаются:

- `.codex/skills/<prefix>-project-workflow/SKILL.md`
- `.codex/skills/<prefix>-api-*/SKILL.md`
- `.codex/skills/<prefix>-api-*/references/TODO.md` (только если отсутствует; не перезаписывать)

### 5.7. Безопасное обновление overlay skills (КЛЮЧЕВО)

**Требование:** overlays нельзя перезатирать молча.

Политика по умолчанию = **C**:

- overwrite overlay **только если он не изменён** с момента последней генерации.

Механизм:

- bootstrap хранит в `.agent/skills_state.json` словарь `overlay_generated_hashes`, ключ: `"<target>/<overlay_name>"`, значение: sha256 текущего `SKILL.md` на момент генерации.
- при повторном init:

  - если overlay отсутствует → создать и записать hash
  - если overlay существует:

    - если включён `--force-overwrite-overlays` → сделать backup `SKILL.md.bootstrap.bak`, перезаписать, обновить hash
    - если **нет** `prev_generated_hash`:

      - по умолчанию: **не трогать**, записать новый кандидат в `.agent/overlays_pending/<target>/<overlay>/SKILL.md`, добавить TODO
      - если включён `--adopt-existing-overlays` → “усыновить” текущий файл как baseline (записать его hash), не перезаписывать
    - если `current_hash == prev_generated_hash` → safe overwrite (перезаписать новым контентом, обновить hash)
    - если `current_hash != prev_generated_hash` → файл модифицирован человеком, не перезаписывать; записать кандидат в `.agent/overlays_pending/...`, добавить TODO, hash оставить прежним

### 5.8. Артефакты bootstrap (state и отчёты)

Bootstrap должен записывать:

- `.agent/project_profile.json` — детект и inferred команды
- `.agent/skills_state.json` — registry git/ref/commit, targets, project_prefix, install_method, registry_skills_selected, registry_skills_installed, registry_skills_skipped, unsupported_targets, overlays_skipped, cleaned_registry_skills, overlay_generated_hashes
- `.agent/skills_todo.md` — список TODO (проверить команды, заполнить API, merge overlay candidates и т.д.)
- `.agent/overlays_pending/...` — кандидаты overlay файлов, если нельзя перезаписать текущие

---

## 6) Требования (Non-functional)

- **Trusted only:** bootstrap не должен скачивать skills из внешних каталогов/маркетплейсов.
- **Stdlib only:** скрипт `bootstrap.py` должен работать на Python3 без внешних зависимостей.
- **Idempotent:** повторный запуск даёт предсказуемый результат.
- **Безопасность:** не запускать произвольный код из интернета; только git clone вашего registry.
- **Контекст-гигиена:** большие данные (например OpenAPI) не вставлять в SKILL.md; в v0.1 только TODO/скелет.

---

## 7) Репозиторий skillregistry: структура и файлы

### 7.1. Структура

```
skillregistry/
  skills/
    project-bootstrap/
      SKILL.md
      scripts/bootstrap.py
    tdd-loop/SKILL.md
    code-review/SKILL.md
    api-openapi-generic/SKILL.md
    lang-go/SKILL.md
    lang-rust/SKILL.md
    lang-python/SKILL.md
    lang-ts/SKILL.md
  templates/
    project-workflow.SKILL.template.md
    api-skeleton.SKILL.template.md
  catalog/
    skillsets.json
  README.md
```

### 7.2. Минимальные registry skills

В v0.1 допустимы короткие заглушки (будем улучшать позже), главное — наличие SKILL.md и корректный `name`.

---

## 8) Интерфейс запуска (CLI)

### 8.1. Скрипт

Запуск из проекта:

```bash
python3 .agent/skillregistry/skills/project-bootstrap/scripts/bootstrap.py init \
  --skillregistry-git <GIT_OR_PATH> \
  --skillregistry-ref <REF> \
  --targets codex,claude
```

Флаги:

- `--install-method skill-installer|local`
- `--force-overwrite-registry-skills`
- `--force-overwrite-overlays`
- `--force-create-overlays`
- `--adopt-existing-overlays`
- `--project-prefix <prefix>`
- `--no-clean-stale-registry-skills`

`claude` target сейчас пропускается и фиксируется в TODO/state.

Переменные окружения (альтернатива флагам):

- `SKILLREGISTRY_GIT`
- `SKILLREGISTRY_REF`

---

## 9) Git-гигиена (для проектных репозиториев)

### 9.1. Что коммитить

- Коммитить overlays (<prefix>-project-workflow, <prefix>-api-*) — **да** (они часть проектного знания)
- Не коммитить `.agent/skillregistry` — **нет** (это клон trusted registry)

### 9.2. Рекомендованный .gitignore snippet для проектов

```gitignore
# internal clone
.agent/skillregistry/

# volatile state
.agent/project_profile.json
.agent/skills_state.json
.agent/skills_todo.md
.agent/overlays_pending/

# Keep overlays, ignore registry skills (optional policy)
.codex/skills/*
!.codex/skills/*-project-workflow/**
!.codex/skills/project-workflow/**
!.codex/skills/*-api-*/**
!.codex/skills/api-*/**

# Claude (currently skipped, placeholder for later)
.claude/skills/*
!.claude/skills/*-project-workflow/**
!.claude/skills/project-workflow/**
!.claude/skills/*-api-*/**
!.claude/skills/api-*/**
```

---

## 10) План реализации (шаги для агента)

### Шаг A: создать skillregistry repo

1. `git init` в `/Users/vi/projects/skillregistry`
2. создать структуру директорий (см. раздел 7.1)
3. добавить `catalog/skillsets.json`
4. добавить templates:

   - `templates/project-workflow.SKILL.template.md`
   - `templates/api-skeleton.SKILL.template.md`
5. добавить минимальные registry skills (SKILL.md для baseline + языковых)
6. добавить `skills/project-bootstrap/SKILL.md`

### Шаг B: реализовать `bootstrap.py`

Реализовать:

- `ensure_skillregistry()`:

  - clone/fetch/checkout ref
  - commit hash
- `detect_project()`:

  - языки/CI/docker/apis/openapi_files
- `infer_commands()`:

  - Makefile/Taskfile/justfile → иначе defaults по языкам
- `select_registry_skills()` по skillsets.json
- `load_prev_state()` из `.agent/skills_state.json`
- `clean_stale_registry_skills()` по prev_state
- `install_registry_skills()` (skill-installer/local)
- `safe_write_overlay()` с политикой C + флагами
- генерация overlays:

  - `<prefix>-project-workflow` из template
  - `<prefix>-api-*` из template + references/TODO.md (create-if-missing)
- запись артефактов: project_profile.json, skills_state.json, skills_todo.md

### Шаг C: тесты/проверка (минимум)

1. создать временный проект с `go.mod` и `.env.example` содержащим `STRIPE_API_KEY=`
2. запустить bootstrap с `--skillregistry-git /Users/vi/projects/skillregistry`
3. убедиться, что:

   - registry skills поставились в `.codex/skills` (claude пропускается)
   - overlays созданы
   - state/todo записаны
4. модифицировать вручную `.codex/skills/<prefix>-project-workflow/SKILL.md`
5. перезапустить bootstrap → файл не должен перезаписаться, а кандидат должен появиться в `.agent/overlays_pending/...` + TODO

---

## 11) Критерии приёмки (Acceptance Criteria)

### Функциональные

- [ ] skillregistry создан, содержит структуру и файлы по PRD
- [ ] bootstrap init работает в пустом проекте и в git‑репо
- [ ] `.agent/skillregistry` создаётся и обновляется по ref
- [ ] registry skills ставятся в `.codex/skills` (claude пропускается)
- [ ] stale registry skills удаляются по prev_state (если отключение флагом не включено)
- [ ] overlay `<prefix>-project-workflow` создаётся всегда
- [ ] overlay `<prefix>-api-*` создаётся при обнаружении API (или openapi files) хотя бы как skeleton
- [ ] при наличии похожего overlay создание пропускается без `--force-create-overlays`
- [ ] overlay политика C соблюдается:

  - если overlay изменён вручную → не перезаписывать, писать кандидат и TODO
  - если overlay не менялся → перезаписывать и обновлять hash
  - если `--force-overwrite-overlays` → перезаписывать с backup
  - если нет истории и `--adopt-existing-overlays` → принять baseline без перезаписи

### Безопасность/ограничения

- [ ] bootstrap не обращается к внешним каталогам skills
- [ ] `bootstrap.py` без внешних зависимостей

---

## 12) Out of scope (v0.1)

- Автоматический поиск OpenAPI в интернете / парсинг чужих документаций
- Claude plugins/marketplace упаковка
- Установка хуков/subagents/venv (это v0.2+)
- Сложные merge/patch overlays (только кандидат + TODO)

---

## 13) Roadmap (следующие версии)

### v0.2

- OpenAPI enrichment:

  - если найден локальный openapi/swagger файл → копировать в overlay `references/`
  - добавить скрипт `query_openapi.py`, который печатает только нужный endpoint/schemas
- Claude-only enhancements:

  - project hooks для логирования ошибок в файл (без засорения контекста)
  - subagent “postmortem” в отдельном контексте, который обновляет/предлагает улучшения skills

### v0.3

- Переход на Claude plugins для группировки (skills+hooks+agents) из trusted repo
- Автоматическое предложение PR/patch для overlays (без потери ручных правок)

---

## Как лучше использовать PRD в Codex CLI

1) Открой Codex CLI в папке `/Users/vi/projects/skillregistry/`.
2) Дай задачу: “Прочитай PRD и реализуй полностью v0.1, строго следуя требованиям и критериям приёмки. Не используй внешние каталоги. В конце выполни локальный smoke‑test по PRD.”
3) Если нужно больше детализации — добавь Task Breakdown (10–20 пунктов) поверх PRD.
