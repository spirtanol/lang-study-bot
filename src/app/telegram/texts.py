WELCOME_TEXT = (
    "Приветствую. Это бот который поможет вам запоминать слова и расширять "
    "словарный запас английского. Вы можете указать свою таймзону и настроить "
    "расписание, что бы бот напоминал вам о занятиях. Что бы добавить слова "
    "для запоминания достаточно просто отправить их боту, бот сам найдет для "
    "них перевод."
)
QUESTION_TEXT = "Слово: {word}\n{text}"

NO_WORDS_TEXT = "Подходящих слов нет."
NO_STUDY_WORDS_TEXT = "У вас нет слов для повторения, следует пополнить запас."
STUDY_TIME_NO_WORDS_TEXT = (
    "Подошло время занятия, но у вас нет слов для повторения, "
    "следует пополнить запас."
)
ALREADY_IN_PROGRESS_TEXT = "Занятие уже идёт."
START_STUDY_TEXT = "Начнем."
START_PENDING_SESSION_TEXT = "Начнем!"
STUDY_LATER_TEXT = "Позанимаемся в другой раз"

SCHEDULE_TIME_PROMPT = "Введите время в формате H:i, например 12:00."
SCHEDULE_PARSE_FAILED_TEXT = (
    "Не получилось разобрать время. Введите время в формате H:i, например 12:00."
)
NO_SCHEDULE_TEXT = "Расписание не задано."
SCHEDULE_CLEARED_TEXT = "Расписание очищено."
SCHEDULE_CHANGED_TEXT = "Расписание изменено."
SCHEDULE_DAILY = "каждый день в"
SCHEDULE_DAILY_TITLE = "Каждый день в"
TIMEZONE_LABEL = "Таймзона:"

TIMEZONE_PROMPT = (
    "Пришлите город, название таймзоны или смещение, "
    "например Москва, Europe/Moscow, +3 или +2:30."
)
TIMEZONE_PARSE_FAILED_TEXT = (
    "Не получилось разобрать таймзону. Пришлите город, название или смещение, "
    "например Москва, Europe/Moscow, +3 или +2:30."
)
TIMEZONE_SET_TEXT = "Установлена таймзона:"

ADD_WORDS_PROMPT = (
    "Перечислите слова или фразы через запятую, точку с запятой или с новой строки."
)
ADD_WORDS_PARSE_FAILED_TEXT = f"Не получилось разобрать слова. {ADD_WORDS_PROMPT}"
ADDED_WORDS_LABEL = "Добавлено:"
REJECTED_WORDS_LABEL = "Не добавлено:"

CANCELLED_TEXT = "Отменено."

CHECK_FAILED_TEXT = "Не получилось проверить ответ. Попробуй ещё раз."
CORRECT_TEXT = "Верно"
INCORRECT_TEXT = "Неверно."
RUSSIAN_REQUIRED_TEXT = "Нужен перевод на русский."
POSSIBLE_TRANSLATIONS_TEXT = "Возможные переводы:"
SESSION_FINISHED_TEXT = "Занятие завершено, повторены все слова."
SESSION_FINISHED_BY_TIME_TEXT = "Занятие закончено по времени."
SESSION_INTERRUPTED_TEXT = "Занятие прервано."
NO_ACTIVE_SESSION_TEXT = "Нет активного занятия."
SKIPPED_ANSWER = "Не знаю"
REVIEWED_COUNT_LABEL = "Повторили вопросов:"
CORRECT_COUNT_LABEL = "Правильных переводов:"
INCORRECT_COUNT_LABEL = "Неправильных:"
SKIPPED_COUNT_LABEL = "Пропущено:"

STUDY_TIME_TEXT = "Пора позаниматься."
SESSION_MISSED_TIMEOUT_TEXT = "Занятие не состоялось по таймауту."
SESSION_FINISHED_TIMEOUT_TEXT = "Занятие завершено по таймауту."
SESSION_MISSED_DUE_TIMEOUT_TEXT = "Занятие не состоялось из-за таймаута."
