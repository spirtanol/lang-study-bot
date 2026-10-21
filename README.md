# Lang Study Assistant

Telegram-бот для коротких занятий английским: словарь, перевод слов и фраз,
адаптивное повторение и напоминания по расписанию.

Это также учебный проект по [LangGraph](https://github.com/langchain-ai/langgraph):
проверка ответа и отбор новых слов смоделированы графами, а правила занятия,
таймеры и прогресс остаются в коде приложения.

Живой бот: [**@en_lang_study_bot**](https://t.me/en_lang_study_bot)

## Что умеет

- принять слова и фразы в общий каталог и в словарь пользователя;
- провести занятие: примеры употребления, перевод на русский, оценка ответа;
- показывать чаще то, что усвоено хуже;
- напомнить о занятии в выбранное время с учётом часового пояса;
- разобрать время, таймзону и перевод из свободного текста через LLM.

## Стек

| Слой | Технологии |
| --- | --- |
| Язык и пакеты | Python 3.13, Poetry |
| HTTP | FastAPI, uvicorn |
| Telegram | aiogram, webhook |
| Данные | PostgreSQL, SQLAlchemy, Alembic |
| Очереди | RabbitMQ, Taskiq |
| LLM | Ollama или Gemini через общий `LLMProvider`, LangGraph |
| Запуск | Docker Compose, Make |

Разработка и установка зависимостей — только в контейнерах.

## Архитектура

Слоистый монолит: webhook и CLI вызывают одни и те же сервисы, состояние
живёт в PostgreSQL, долгие шаги уходят в очереди Taskiq.

Подробнее: [ARCHITECTURE.md](ARCHITECTURE.md).

## Запуск

Нужны Docker, Docker Compose и Make. Зависимости Python ставятся внутри
контейнера, на хост их ставить не нужно.

1. Скопируйте окружение и заполните секреты:

   ```bash
   cp .env.example .env
   ```

   Обязательные поля:

   - `TELEGRAM_BOT_TOKEN` — токен бота;
   - `TELEGRAM_BOT_URL` — публичный HTTPS-адрес, до которого Telegram достучится.
     При старте webhook регистрируется как `{TELEGRAM_BOT_URL}/hook`.
     Секрет заголовка `X-Telegram-Bot-Api-Secret-Token` генерируется в процессе
     и передаётся Telegram, в `.env` его нет;
   - `CONTACT_TELEGRAM_USERNAME` — имя в Telegram без `@` для команды `/contacts`;
   - `CONTACT_EMAIL` — почта для команды `/contacts`;
   - `UID` и `GID` — пользователь хоста, от имени которого пишутся файлы в volume.

   Тексты `/start` и `/contacts` можно заменить без правки кода: скопируйте
   `texts.local.toml.example` в `texts.local.toml` и измените строки. Файл
   не коммитится. В `CONTACTS_TEXT` оставьте подстановку `{telegram}` и `{email}`.
   Перевод строки перед закрывающими `"""` при чтении отбрасывается.

2. Выберите LLM-провайдера в `.env`.

   Gemini:

   ```env
   LLM_PROVIDER=gemini
   GEMINI_API_KEY=...
   LLM_MODEL=gemini-flash-latest
   ```

   Локальная Ollama:

   ```env
   LLM_PROVIDER=ollama
   LLM_MODEL=qwen3:4b
   ```

3. Соберите и поднимите сервисы, поставьте extra выбранного провайдера и
   примените миграции:

   ```bash
   make up
   make shell
   poetry install -E gemini   # или: poetry install -E ollama
   exit
   make migrate
   ```

   `make up` поднимает `web`, планировщик, воркеры, PostgreSQL, RabbitMQ,
   Ollama и просмотр логов Dozzle.

4. Для Ollama скачайте модель:

   ```bash
   make ollama-pull
   ```

   Другая модель: `make ollama-pull MODEL=имя:тег`.

Порт HTTP по умолчанию — `127.0.0.1:8000`. Для локального бота нужен туннель
с публичным HTTPS на этот порт, иначе Telegram не доставит webhook.

Полезные команды:

| Команда | Назначение |
| --- | --- |
| `make up` / `make down` | поднять или остановить стек |
| `make migrate` | применить миграции Alembic |
| `make shell` | bash в контейнере `web` |
| `make chat` | то же занятие через CLI, без Telegram |
| `make logs-web` | логи webhook |
| `make logs-worker` / `make logs-tg-worker` | логи очередей |

Compose для разработки: `docker-compose.dev.yml`. Makefile использует его
по умолчанию.
