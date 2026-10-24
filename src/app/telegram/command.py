from enum import StrEnum


class TelegramCommand(StrEnum):
    START = "start"
    CONTACTS = "contacts"
    SCHEDULE = "schedule"
    SETUP_SCHEDULE = "setup_schedule"
    CLEAR_SCHEDULE = "clear_schedule"
    TIMEZONE = "timezone"
    CANCEL = "cancel"
    ADD_WORDS = "add_words"
    ADD_BATCH = "add_batch"
    STUDY = "study"
    DONT_KNOW = "dont_know"
    FINISH = "finish"


TELEGRAM_COMMAND_DESCRIPTIONS: dict[TelegramCommand, str] = {
    TelegramCommand.START: "Начать",
    TelegramCommand.CONTACTS: "Контакты",
    TelegramCommand.SCHEDULE: "Показать расписание",
    TelegramCommand.SETUP_SCHEDULE: "Настроить расписание",
    TelegramCommand.CLEAR_SCHEDULE: "Очистить расписание",
    TelegramCommand.TIMEZONE: "Настроить таймзону",
    TelegramCommand.CANCEL: "Отменить",
    TelegramCommand.ADD_WORDS: "Добавить слова",
    TelegramCommand.STUDY: "Начать занятие",
    TelegramCommand.DONT_KNOW: "Не знаю",
    TelegramCommand.FINISH: "Закончить занятие",
}

TELEGRAM_COMMANDS_CAPTIONS: dict[TelegramCommand, str] = {
    TelegramCommand.DONT_KNOW: "Не знаю",
    TelegramCommand.CANCEL: "Отменить",
    TelegramCommand.FINISH: "Закончить",
}
