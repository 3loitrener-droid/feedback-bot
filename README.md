# Feedback Assistant

Гибридный инструмент для руководителей: Telegram-бот + веб-кабинет для фиксации фидбэка по сотрудникам, разметки по матрице ожиданий и подготовки evidence-based summary для performance review.

---

## Архитектура

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│ Telegram Bot │───▶│  FastAPI API  │───▶│  PostgreSQL  │
└─────────────┘    │  (Python)     │    └─────────────┘
                   └──────┬───────┘    ┌─────────────┐
┌─────────────┐           │            │    Redis     │
│  Next.js UI  │──────────┘            └─────────────┘
└─────────────┘           │
                   ┌──────▼───────┐
                   │ Claude API   │
                   │ (Anthropic)  │
                   └──────────────┘
```

**Backend:** Python 3.12 / FastAPI / SQLAlchemy 2.0 / Alembic  
**Bot:** python-telegram-bot 21  
**LLM:** Anthropic Claude (claude-sonnet-4-6)  
**Frontend:** Next.js 14 / TypeScript / Tailwind CSS / React Query  
**DB:** PostgreSQL 16 + Redis 7  

---

## Быстрый старт

### 1. Клонировать и настроить окружение

```bash
cp .env.example .env
```

Заполнить в `.env`:

| Переменная | Описание |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Токен от @BotFather |
| `ANTHROPIC_API_KEY` | API-ключ Anthropic |
| `SECRET_KEY` | Случайная строка ≥32 символа |
| `POSTGRES_PASSWORD` | Пароль БД |

### 2. Запуск через Docker Compose

```bash
bash scripts/start.sh
```

Или вручную:

```bash
docker compose up --build -d
```

После запуска:
- **API docs:** http://localhost:8000/api/docs
- **Веб-кабинет:** http://localhost:3000

### 3. Локальный запуск (разработка)

```bash
bash scripts/dev.sh
```

Требует: Python 3.12+, pip, npm

---

## Демо-аккаунты

После первого запуска seed автоматически создаёт:

| Роль | Email |
|---|---|
| Manager | alexey@company.com |
| HRBP | maria@company.com |
| Admin | dmitry@company.com |

Войти: запросить magic link через `/auth` в веб-кабинете или через `/start` в боте.

---

## Структура проекта

```
.
├── backend/
│   ├── app/
│   │   ├── api/routes/      # FastAPI эндпоинты
│   │   ├── bot/             # Telegram-бот (FSM)
│   │   │   └── handlers/    # Сценарии 1–5
│   │   ├── core/            # Auth, security
│   │   ├── db/              # SQLAlchemy session
│   │   ├── llm/             # Claude API, промпты
│   │   ├── models/          # SQLAlchemy модели
│   │   ├── schemas/         # Pydantic схемы
│   │   ├── scripts/         # seed.py
│   │   └── services/        # SummaryService
│   └── alembic/             # Миграции БД
├── frontend/
│   └── src/
│       ├── app/
│       │   ├── auth/        # Страница входа (magic link)
│       │   └── (dashboard)/
│       │       ├── team/    # Список команды со статистикой
│       │       ├── employees/[id]/  # Карточка сотрудника
│       │       ├── timeline/        # Хронология всех комментариев
│       │       └── admin/           # Матрица критериев, периоды
│       ├── components/
│       ├── lib/             # API-клиент, утилиты
│       └── types/           # TypeScript типы
├── nginx/
├── scripts/
└── docker-compose.yml
```

---

## API эндпоинты

```
POST   /api/auth/magic-link          Запросить magic link
GET    /api/auth/verify?token=...    Верифицировать и получить JWT
POST   /api/auth/telegram-link       Привязать Telegram к email
POST   /api/auth/telegram-verify     Авторизация по telegram_id

GET    /api/employees/               Список команды
GET    /api/employees/stats          Список с метриками
GET    /api/employees/{id}           Карточка сотрудника

POST   /api/feedback/                Создать комментарий
GET    /api/feedback/                Список с фильтрами
PATCH  /api/feedback/{id}            Обновить статус
DELETE /api/feedback/{id}            Soft delete
POST   /api/feedback/{id}/mappings   Добавить связку
PATCH  /api/feedback/{id}/mappings/{mid}  Обновить связку
DELETE /api/feedback/{id}/mappings/{mid}  Удалить связку

GET    /api/criteria/                Матрица критериев
POST   /api/criteria/                Создать критерий (admin)
PATCH  /api/criteria/{id}            Обновить критерий (admin)

GET    /api/periods/                 Список периодов
POST   /api/periods/                 Создать период (admin)

POST   /api/summary/generate         Запустить генерацию summary
GET    /api/summary/                 Получить summary

POST   /api/llm/analyze              Анализ комментария через LLM

GET    /api/export/summary           Экспорт summary в HTML
```

---

## Telegram-бот: сценарии

| Кнопка | Сценарий |
|---|---|
| 📝 Оставить фидбэк | FSM: выбор сотрудника → текст → разметка (авто/ручная/без) → подтверждение |
| 📊 Посмотреть summary | Выбор сотрудника + период → LLM-summary с evidence |
| 📋 История | Хронология комментариев по сотруднику |
| 🗣 Подготовиться к 1:1 | Темы, вопросы, зоны роста |
| 📄 Performance Review | Структурированный отчёт с рекомендацией |
| 🌐 Открыть веб-кабинет | Ссылка на веб-интерфейс |

---

## LLM-логика

**Анализ комментария** (`POST /api/llm/analyze`):
- Вход: `original_text` + контекст сотрудника + матрица критериев
- LLM разбивает на фрагменты, сопоставляет с критериями, предлагает оценку
- `original_text` хранится неизменно — LLM только предлагает разметку
- Руководитель подтверждает или редактирует каждую связку

**Генерация summary** (`POST /api/summary/generate`):
- Принимает все размеченные комментарии за период
- Формирует: сильные зоны, зоны роста, паттерны, рекомендацию, evidence (цитаты)
- Evidence — только оригинальные слова руководителя

---

## Матрица критериев (18 критериев)

1. Эффективный администратор
2. Адепт эффективного внедрения ИИ
3. Персональные качества
4. Принимает решения как ко-фаундер ⭐
5. Маркетирование продукта
6. Продукт для клиента ⭐
7. Сколачивание сильной команды ⭐
8. Визионерство
9. Концептуальное мышление
10. Ясность стратегии ⭐
11. Качество приоритизации ⭐
12. Выполнение продуктовых OKR ⭐
13. Предсказуемость execution ⭐
14. Зрелость процессов и функции
15. Работа со стейкхолдерами ⭐
16. Ответственность ⭐
17. Фокусы
18. Артефакты

⭐ — ключевые критерии (влияют на рекомендацию оценки)

---

## Права доступа

| Роль | Видимость |
|---|---|
| `manager` | Только своя команда (по ManagerEmployeeVisibility) |
| `hrbp` | Все сотрудники, агрегированная аналитика |
| `admin` | Полный доступ + управление матрицей и периодами |
| `employee` | Нет доступа к черновикам менеджера |

---

## Принципы, заложенные в код

1. **`original_text` — immutable.** Поле не обновляется после создания (защита на уровне логики).
2. **LLM — только предложение.** Поле `manager_confirmed` обязательно для финального учёта в summary.
3. **Row-level security.** Все запросы фильтруются по `manager_id` или visibility-таблице.
4. **Один комментарий — несколько связок.** Таблица `feedback_criterion_mappings` (many-to-many с fragment+rating).
5. **Evidence в summary — только raw-цитаты.** LLM инструктирована не перефразировать.
