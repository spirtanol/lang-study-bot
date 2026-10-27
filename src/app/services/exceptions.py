class ActiveStudySessionNotFoundError(Exception):
    pass


class NoStudyWordsError(Exception):
    def __init__(self) -> None:
        super().__init__("Нет слов для повторения.")


class WordNotAdded(Exception):
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


class ScheduleSlotTooCloseError(Exception):
    def __init__(self) -> None:
        super().__init__("Слот слишком близко к уже существующему.")


class ScheduleSlotNotFoundError(Exception):
    def __init__(self) -> None:
        super().__init__("Слот расписания не найден.")


class PendingQuestionNotFoundError(Exception):
    def __init__(self) -> None:
        super().__init__("Нет текущего вопроса.")


class UserVersionError(Exception):
    def __init__(self) -> None:
        super().__init__("Версия пользователя устарела.")


class UserBusyError(Exception):
    def __init__(self) -> None:
        super().__init__("Пользователь занят.")


class TelegramSendError(Exception):
    def __init__(self) -> None:
        super().__init__("Не удалось отправить сообщение в Telegram.")
