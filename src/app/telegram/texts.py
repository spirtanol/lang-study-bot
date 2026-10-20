CONTACTS_TEXT = (
    "💬 **Обратная связь и поддержка**\n\n"
    "Если у вас есть вопросы, предложения по улучшению или вы обнаружили ошибку, "
    "буду рад любой обратной связи!\n\n"
    "✈️ **Telegram:** @{telegram}\n"
    "📧 **Email:** {email}\n\n"
    "Пишите в любое время, постараюсь ответить как можно быстрее!"
)

WELCOME_TEXT = (
    "Привет! 👋 Это бот для запоминания английских слов и расширения словарного запаса.\n\n"
    "⏰ Вы можете указать свою таймзону и настроить расписание, чтобы бот напоминал о занятиях.\n"
    "📚 Перед началом добавьте слова для повторения с помощью команды /add_words."
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