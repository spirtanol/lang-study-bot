from enum import IntEnum, StrEnum


class UserIntent(StrEnum):
    SCHEDULE = "schedule"
    ANSWER = "answer"
    STUDY = "study"
    UNKNOWN = "unknown"
    ADD_WORDS = "add_words"
    TIMEZONE = "timezone"


class UserStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    BLOCKED = "blocked"


class StudySessionStatus(StrEnum):
    COMPLETED = "completed"
    IN_PROGRESS = "in_progress"
    PENDING = "pending"
    INTERRUPTED = "interrupted"
    DEFERRED = "deferred"
    DEFERRED_2 = "deferred_2"
    REJECTED = "rejected"
    TIMED_OUT = "timed_out"


class StartSessionResult(StrEnum):
    READY = "ready"
    ALREADY_READY = "already_ready"
    NOT_NOW = "not_now"


class StudyAttemptStatus(StrEnum):
    CORRECT = "correct"
    INCORRECT = "incorrect"
    PENDING = "pending"
    TIMED_OUT = "timed_out"
    SKIPPED = "skipped"


class FamiliarityLevel(IntEnum):
    BAD = 10
    GOOD = 30
