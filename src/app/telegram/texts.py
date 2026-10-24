import tomllib
from pathlib import Path

CONTACTS_TEXT = (
    "💬 **Обратная связь и поддержка**\n\n"
    "Если у вас есть вопросы, предложения по улучшению или вы обнаружили ошибку, "
    "буду рад любой обратной связи!\n\n"
    "✈️ **Telegram:** @{telegram}\n"
    "📧 **Email:** {email}\n\n"
)

WELCOME_TEXT = (
    "Привет! 👋 Это бот-словарь для английских слов.\n\n"
    "📖 Пришлите слово — бот переведёт его, и перевод можно сохранить на повтор.\n"
    "📚 Слова для повторения также можно добавить командой /add_words.\n"
    "⏰ Укажите таймзону и настройте расписание, чтобы бот напоминал о занятиях."
)

QUESTION_TEXT = "🇬🇧 **Слово:** {word}\n{text}"

NO_WORDS_TEXT = "Подходящих слов нет."
NO_STUDY_WORDS_TEXT = "У вас нет слов для повторения. Добавьте новые слова с помощью /add_words."
STUDY_TIME_NO_WORDS_TEXT = (
    "⏰ Подошло время занятия, но у вас нет слов для повторения. "
    "Пополните запас с помощью /add_words."
)
ALREADY_IN_PROGRESS_TEXT = "Занятие уже идёт!"
START_STUDY_TEXT = "Начнём! 🚀"
START_PENDING_SESSION_TEXT = "Начнём! 🔥"
STUDY_LATER_TEXT = "Позанимаемся в другой раз 👍"

SCHEDULE_TIME_PROMPT = "Введите время в формате HH:MM (например, 12:00 или 09:30):"
SCHEDULE_PARSE_FAILED_TEXT = (
    "Не получилось разобрать время. Пожалуйста, введите его в формате HH:MM (например, 12:00)."
)
NO_SCHEDULE_TEXT = "Расписание не задано."
SCHEDULE_CLEARED_TEXT = "🗑 Расписание очищено."
SCHEDULE_CHANGED_TEXT = "✅ Расписание изменено."
SCHEDULE_DAILY = "каждый день в"
SCHEDULE_DAILY_TITLE = "Каждый день в"
TIMEZONE_LABEL = "🌐 Таймзона:"

TIMEZONE_PROMPT = (
    "Пришлите название города, таймзону или смещение.\n"
    "Например: `Москва`, `Europe/Moscow`, `+3` или `+2:30`."
)
TIMEZONE_PARSE_FAILED_TEXT = (
    "Не удалось определить таймзону. Пришлите название города, таймзону или смещение.\n"
    "Например: `Москва`, `Europe/Moscow`, `+3` или `+2:30`."
)
TIMEZONE_SET_TEXT = "🌐 Установлена таймзона:"

ADD_WORDS_PROMPT = (
    "Отправьте слова или фразы через запятую, точку с запятой или с новой строки."
)
ADD_WORDS_ACCEPTED_TEXT = (
    "Слова приняты к добавлению. Это может занять несколько секунд."
)
WORDS_ADDED_TEXT = "Слова добавлены в словарь."
WORD_BATCH_EXPIRED_TEXT = "Этот список уже недоступен."
ADD_WORDS_PARSE_FAILED_TEXT = f"Не удалось разобрать слова. {ADD_WORDS_PROMPT}"
ADDED_WORDS_LABEL = "✅ Добавлено:"
REJECTED_WORDS_LABEL = "❌ Не добавлено:"

CANCELLED_TEXT = "🚫 Отменено."

CHECK_FAILED_TEXT = "⚠️ Не удалось проверить ответ. Попробуйте ещё раз."
MODEL_UNAVAILABLE_TEXT = (
    "🤖 Модель временно недоступна. Пожалуйста, подождите и попробуйте ещё раз."
)
CORRECT_TEXT = "✅ Верно!"
INCORRECT_TEXT = "❌ Неверно."
RUSSIAN_REQUIRED_TEXT = "Нужен перевод на русский язык."
POSSIBLE_TRANSLATIONS_TEXT = "💡 Возможные переводы:"
SESSION_FINISHED_TEXT = "🎉 Занятие завершено! Все слова повторены."
SESSION_FINISHED_BY_TIME_TEXT = "⏱ Занятие завершено по времени."
SESSION_INTERRUPTED_TEXT = "⏸ Занятие прервано."
NO_ACTIVE_SESSION_TEXT = "Сейчас нет активного занятия."
SKIPPED_ANSWER = "Не знаю 🤷‍♂️"
REVIEWED_COUNT_LABEL = "📊 Повторено вопросов:"
CORRECT_COUNT_LABEL = "✅ Правильных переводов:"
INCORRECT_COUNT_LABEL = "❌ Неправильных:"
SKIPPED_COUNT_LABEL = "⏭ Пропущено:"

STUDY_TIME_TEXT = "🔔 Пора позаниматься!"
SESSION_MISSED_TIMEOUT_TEXT = "⏱ Занятие не состоялось (истёк срок ожидания)."
SESSION_FINISHED_TIMEOUT_TEXT = "⏱ Занятие завершено по таймауту."
SESSION_MISSED_DUE_TIMEOUT_TEXT = "⏱ Занятие пропущено из-за таймаута."

_OVERRIDABLE_TEXTS = frozenset({"CONTACTS_TEXT", "WELCOME_TEXT"})


def _apply_local_texts() -> None:
    global CONTACTS_TEXT, WELCOME_TEXT

    path = Path.cwd() / "texts.local.toml"
    if not path.is_file():
        return

    overrides = tomllib.loads(path.read_text(encoding="utf-8"))
    unknown = sorted(set(overrides) - _OVERRIDABLE_TEXTS)
    if unknown:
        names = ", ".join(unknown)
        raise ValueError(f"В texts.local.toml неизвестные ключи: {names}")

    applied: dict[str, str] = {}
    for key, value in overrides.items():
        if not isinstance(value, str):
            raise ValueError(f"texts.local.toml: {key} должен быть строкой")
        applied[key] = value.removesuffix("\n")

    contacts = applied.get("CONTACTS_TEXT")
    if contacts is not None:
        try:
            contacts.format(telegram="telegram", email="email")
        except (IndexError, KeyError, ValueError) as exc:
            raise ValueError(
                "CONTACTS_TEXT в texts.local.toml не подставляется "
                "через {telegram} и {email}"
            ) from exc
        CONTACTS_TEXT = contacts

    welcome = applied.get("WELCOME_TEXT")
    if welcome is not None:
        WELCOME_TEXT = welcome


_apply_local_texts()