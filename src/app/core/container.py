from contextlib import asynccontextmanager
from contextvars import ContextVar
from collections.abc import AsyncIterator
from datetime import timedelta
from functools import cached_property
from typing import assert_never

from app.core.config import AppSettings, get_config
from app.core.db import AsyncSession, get_engine, get_session_maker
from app.defs import LEASE
from app.graphs import AddWordsGraph, AnswerCheckGraph
from app.llm import LLMProvider
from app.repositories import (
    ChatMessageRepository,
    StudyAttemptRepository,
    StudyScheduleSlotRepository,
    StudySessionRepository,
    TelegramUpdateRepository,
    UserRepository,
    VocabularyItemRepository,
    WordRepository,
)
from app.services import (
    ChatMessageService,
    EventService,
    LanguageModelService,
    SchedulerService,
    StudyScheduleService,
    StudySessionService,
    TelegramMessageService,
    TelegramUpdateService,
    UserReplyService,
    UserService,
    VocabularyService,
    WordService,
)
from app.telegram import TelegramClient


_session_var: ContextVar[AsyncSession | None] = ContextVar("session", default=None)


class Container:
    def __init__(self, config: AppSettings):
        self.config = config

    def get_session(self) -> AsyncSession:
        session = _session_var.get()
        if session is None:
            raise RuntimeError("Сессия не инициализирована. Вызовите метод внутри контекста `transaction()`")

        return session

    @cached_property
    def user_repository(self) -> UserRepository:
        return UserRepository(self.get_session)

    @cached_property
    def user_service(self) -> UserService:
        return UserService(
            repository=self.user_repository,
            slots=self.study_schedule_slot_repository,
            sessions=self.study_session_repository,
            attempts=self.study_attempt_repository,
            transaction=self.transaction,
            session_timeout=timedelta(minutes=self.config.session_timeout_minutes),
        )

    @cached_property
    def study_schedule_slot_repository(self) -> StudyScheduleSlotRepository:
        return StudyScheduleSlotRepository(self.get_session)

    @cached_property
    def study_schedule_service(self) -> StudyScheduleService:
        return StudyScheduleService(
            repository=self.study_schedule_slot_repository,
            users=self.user_repository,
            user_service=self.user_service,
            transaction=self.transaction,
            slot_gap_minutes=self.config.schedule_slot_gap_minutes,
        )

    @cached_property
    def study_session_repository(self) -> StudySessionRepository:
        return StudySessionRepository(self.get_session)

    @cached_property
    def vocabulary_item_repository(self) -> VocabularyItemRepository:
        return VocabularyItemRepository(self.get_session)

    @cached_property
    def vocabulary_service(self) -> VocabularyService:
        return VocabularyService(
            repository=self.vocabulary_item_repository,
            words=self.word_service,
            transaction=self.transaction,
        )

    @cached_property
    def study_attempt_repository(self) -> StudyAttemptRepository:
        return StudyAttemptRepository(self.get_session)

    @cached_property
    def llm_provider(self) -> LLMProvider:
        match self.config.llm_provider:
            case "ollama":
                try:
                    from app.llm.ollama import OllamaProvider
                except ImportError as error:
                    raise RuntimeError(
                        "Провайдер ollama недоступен. Установите зависимость: poetry install -E ollama"
                    ) from error
                return OllamaProvider(
                    model=self.config.llm_model,
                    base_url=self.config.llm_base_url,
                    temperature=self.config.llm_temperature,
                    context_size=self.config.llm_context_size,
                    timeout_seconds=self.config.llm_timeout_seconds,
                )
            case "gemini":
                try:
                    from app.llm.gemini import GeminiProvider
                except ImportError as error:
                    raise RuntimeError(
                        "Провайдер gemini недоступен. Установите зависимость: poetry install -E gemini"
                    ) from error
                return GeminiProvider(
                    model=self.config.llm_model,
                    api_key=self.config.gemini_api_key,
                    temperature=self.config.llm_temperature,
                    timeout_seconds=self.config.llm_timeout_seconds,
                )
            case _ as unexpected:
                assert_never(unexpected)

    @cached_property
    def language_model_service(self) -> LanguageModelService:
        return LanguageModelService(
            self.llm_provider,
            rate_limit_retries=self.config.llm_rate_limit_retries,
            rate_limit_max_delay_seconds=self.config.llm_rate_limit_max_delay_seconds,
        )

    @cached_property
    def add_words_graph(self) -> AddWordsGraph:
        return AddWordsGraph(self.language_model_service)

    @cached_property
    def answer_check_graph(self) -> AnswerCheckGraph:
        return AnswerCheckGraph(self.language_model_service)

    @cached_property
    def word_repository(self) -> WordRepository:
        return WordRepository(self.get_session)

    @cached_property
    def word_service(self) -> WordService:
        return WordService(
            repository=self.word_repository,
            add_words=self.add_words_graph,
            transaction=self.transaction,
        )

    @cached_property
    def study_session_service(self) -> StudySessionService:
        return StudySessionService(
            repository=self.study_session_repository,
            vocabulary_items=self.vocabulary_item_repository,
            study_attempts=self.study_attempt_repository,
            users=self.user_repository,
            language_model=self.language_model_service,
            answer_check=self.answer_check_graph,
            transaction=self.transaction,
            session_duration=timedelta(
                minutes=self.config.session_duration_minutes,
            ),
        )

    @cached_property
    def chat_message_repository(self) -> ChatMessageRepository:
        return ChatMessageRepository(self.get_session)

    @cached_property
    def chat_message_service(self) -> ChatMessageService:
        return ChatMessageService(
            messages=self.chat_message_repository,
            transaction=self.transaction,
            retention_days=self.config.chat_message_retention_days,
        )

    @cached_property
    def telegram_update_repository(self) -> TelegramUpdateRepository:
        return TelegramUpdateRepository(self.get_session)

    @cached_property
    def telegram_client(self) -> TelegramClient:
        return TelegramClient(
            token=self.config.telegram_bot_token,
            api_uri=self.config.telegram_api_uri,
        )

    @cached_property
    def telegram_message_service(self) -> TelegramMessageService:
        return TelegramMessageService(
            client=self.telegram_client,
            messages=self.chat_message_service,
        )

    @cached_property
    def telegram_update_service(self) -> TelegramUpdateService:
        return TelegramUpdateService(
            updates=self.telegram_update_repository,
            transaction=self.transaction,
        )

    @cached_property
    def event_service(self) -> EventService:
        return EventService()

    @cached_property
    def scheduler_service(self) -> SchedulerService:
        return SchedulerService(
            users=self.user_repository,
            events=self.event_service,
            transaction=self.transaction,
            lease=LEASE,
        )

    @cached_property
    def user_reply_service(self) -> UserReplyService:
        return UserReplyService(
            sessions=self.study_session_repository,
            attempts=self.study_attempt_repository,
            study_sessions=self.study_session_service,
            language_model=self.language_model_service,
            users=self.user_repository,
            user_service=self.user_service,
            schedule=self.study_schedule_service,
            vocabulary=self.vocabulary_service,
            transaction=self.transaction,
            contact_telegram_username=self.config.contact_telegram_username,
            contact_email=self.config.contact_email,
        )

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[None]:
        if _session_var.get() is not None:
            yield
            return

        engine = get_engine(self.config.database_url, self.config.debug)
        session_maker = get_session_maker(engine)
        session = session_maker()
        token = _session_var.set(session)
        try:
            yield
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
            _session_var.reset(token)


async def get_container() -> AsyncIterator[Container]:
    container = Container(
        config=get_config()
    )
    yield container


get_context_container = asynccontextmanager(get_container)
