import asyncio
import logging
import random
import re
from collections.abc import Sequence
from datetime import time
from functools import lru_cache
from time import perf_counter
from typing import TypeVar
from zoneinfo import available_timezones

from pydantic import BaseModel, Field

from app.llm import (
    LLMError,
    LLMMessage,
    LLMProvider,
    LLMRateLimitError,
    LLMResponseError,
    LLMUnavailableError,
)
from app.schemas.llm import TranslationVerdict, VerdictReview

ASK_TRANSLATION_TEXT = "Напиши перевод."
WORD_USAGE_SYSTEM_PROMPT = (
    "Write exactly two short English sentences. "
    "Each sentence must use the given word or phrase naturally. "
    "Do not translate it and do not add any other text."
)
TRANSLATION_CHECK_SYSTEM_PROMPT = (
    "Check a learner's translation of an English word or phrase into Russian. "
    "Set is_russian to true only if the answer is in Russian. "
    "Set is_correct to true only if it is a correct Russian translation. "
    "Repeating the English word or phrase is not a translation: "
    "both flags must be false. "
    "When reference translations are given, compare the answer with them. "
    "A match or a close wording of a reference is correct. "
    "A different valid Russian translation is also correct: "
    "the list is not exhaustive. "
    "When the answer is not accepted, write brief remarks in Russian. "
    "When it is accepted, leave remarks empty."
)
VERDICT_REVIEW_SYSTEM_PROMPT = (
    "Review a verdict about a learner's Russian translation "
    "of an English word or phrase. "
    "Set verdict_holds to true only if that verdict correctly judges the answer. "
    "A remark such as «верно» or «правильно» is not a translation. "
    "A verdict that accepts it does not hold. "
    "When the verdict does not hold, remarks are only the correct Russian "
    "translations of the English word or phrase: one to five short items, "
    "separated by commas, and nothing else. "
    "Use the reference translations when they are given. "
    "Do not discuss the learner's answer and do not translate it into English. "
    "«пошатнуться означает потерять равновесие и не соответствует flinch» "
    "is wrong; write «вздрогнуть, дрогнуть». "
    "«Вина означает guilt, а не conscience» is wrong; write «совесть». "
    "When the verdict holds, leave remarks empty."
)
SUGGEST_TRANSLATIONS_SYSTEM_PROMPT = (
    "Give possible Russian translations of the English word or phrase. "
    "Return one to five short translations. "
    "Do not repeat the English text. "
    "Do not add any other text."
)
IS_ENGLISH_WORD_SYSTEM_PROMPT = (
    "Decide whether the text is an English word or phrase. "
    "Set is_english to true for cucumber. "
    "Set is_english to false for asdf. "
    "Return only the structured field."
)
IS_WORD_LIST_SYSTEM_PROMPT = (
    "Decide whether the user message is a vocabulary list of English words "
    "or short phrases. "
    "Items are separated by commas, semicolons, or line breaks. "
    "Set is_word_list to true for «apple, pear» and for one English word "
    "or phrase per line. "
    "Set is_word_list to false for a sentence, a question, or a conversation. "
    "A message in Russian is not a word list. "
    "Return only the structured field."
)
IS_PROPER_NAME_SYSTEM_PROMPT = (
    "Decide whether the text is a proper name: a person, a place, a brand, "
    "or a name from myth. "
    "Set is_proper_name to true for London and Cthulhu. "
    "A common noun that can also be a name is not a proper name: "
    "set is_proper_name to false for pearl and peach. "
    "Return only the structured field."
)
PARSE_CLOCK_TIME_SYSTEM_PROMPT = (
    "Extract a single clock time from the user message: hours and minutes only. "
    "«в двенадцать» means 12:00. "
    "If the message has no time, set hour and minute to null. "
    "Do not invent a time. Return only the structured fields."
)
RESOLVE_TIMEZONE_SYSTEM_PROMPT = (
    "Map the user message to one IANA time zone name, such as Europe/Moscow. "
    "A city, a region, or an offset such as +3 or +2:30 is enough. "
    "If the place or offset is unknown or ambiguous, set timezone to null. "
    "Do not invent a name. Return only the structured field."
)
_CLOCK_TIME = re.compile(r"^(\d{1,2}):(\d{2})$")

logger = logging.getLogger("app.llm")


class WordUsage(BaseModel):
    examples: list[str] = Field(min_length=2, max_length=2)


class WordTranslations(BaseModel):
    translations: list[str] = Field(min_length=1, max_length=5)


class EnglishWord(BaseModel):
    is_english: bool


class WordList(BaseModel):
    is_word_list: bool


class ProperName(BaseModel):
    is_proper_name: bool


class ParsedClockTime(BaseModel):
    hour: int | None = None
    minute: int | None = None


class ParsedTimezone(BaseModel):
    timezone: str | None = None


ResponseT = TypeVar("ResponseT", bound=BaseModel)


class LanguageModelService:
    def __init__(
        self,
        llm: LLMProvider,
        rate_limit_retries: int,
        rate_limit_max_delay_seconds: float,
    ):
        self._llm = llm
        self._rate_limit_retries = rate_limit_retries
        self._rate_limit_max_delay_seconds = rate_limit_max_delay_seconds

    async def _generate_structured(
        self,
        messages: Sequence[LLMMessage],
        response_model: type[ResponseT],
    ) -> ResponseT:
        attempt = 0
        while True:
            started = perf_counter()
            logger.info(
                "Запрос %s %s",
                response_model.__name__,
                [
                    {"role": message.role, "content": message.content}
                    for message in messages
                ],
            )
            try:
                result = await self._llm.generate_structured(messages, response_model)
            except LLMRateLimitError:
                if attempt == self._rate_limit_retries:
                    logger.exception("Исчерпан лимит запросов к модели")
                    raise
                attempt += 1
                logger.warning("Лимит модели, повтор %s", attempt)
                await asyncio.sleep(
                    random.uniform(1, self._rate_limit_max_delay_seconds)
                )
                continue
            except Exception:
                logger.exception("Ошибка модели")
                raise
            elapsed_ms = int((perf_counter() - started) * 1000)
            logger.info("Ответ %s мс %s", elapsed_ms, result.model_dump())
            return result

    async def build_question_text(self, word: str) -> str:
        try:
            usage = await self._generate_structured(
                (
                    LLMMessage(role="system", content=WORD_USAGE_SYSTEM_PROMPT),
                    LLMMessage(role="user", content=word),
                ),
                WordUsage,
            )
        except LLMUnavailableError:
            raise
        except LLMError:
            return ASK_TRANSLATION_TEXT

        examples = [example.strip() for example in usage.examples]
        if any(not example for example in examples):
            return ASK_TRANSLATION_TEXT
        body = "\n".join(examples)
        return f"{body}\n{ASK_TRANSLATION_TEXT}"

    async def check_translation(
        self,
        word: str,
        answer: str,
        translations: tuple[str, ...] = (),
    ) -> TranslationVerdict:
        return await self._generate_structured(
            (
                LLMMessage(role="system", content=TRANSLATION_CHECK_SYSTEM_PROMPT),
                LLMMessage(
                    role="user",
                    content=_answer_message(word, answer, translations),
                ),
            ),
            TranslationVerdict,
        )

    async def review_translation_verdict(
        self,
        word: str,
        answer: str,
        verdict: TranslationVerdict,
        translations: tuple[str, ...] = (),
    ) -> VerdictReview:
        lines = [
            _answer_message(word, answer, translations),
            (
                "Verdict: "
                f"is_russian={str(verdict.is_russian).lower()}, "
                f"is_correct={str(verdict.is_correct).lower()}, "
                f"remarks={verdict.remarks}"
            ),
        ]
        return await self._generate_structured(
            (
                LLMMessage(role="system", content=VERDICT_REVIEW_SYSTEM_PROMPT),
                LLMMessage(role="user", content="\n".join(lines)),
            ),
            VerdictReview,
        )

    async def parse_clock_time(self, text: str) -> time | None:
        match = _CLOCK_TIME.fullmatch(text.strip())
        if match is not None:
            return _clock_time(int(match.group(1)), int(match.group(2)))

        parsed = await self._generate_structured(
            (
                LLMMessage(role="system", content=PARSE_CLOCK_TIME_SYSTEM_PROMPT),
                LLMMessage(role="user", content=text),
            ),
            ParsedClockTime,
        )
        return _clock_time(parsed.hour, parsed.minute)

    async def resolve_timezone(self, text: str) -> str | None:
        found = _iana_name(text)
        if found is not None:
            return found
        parsed = await self._generate_structured(
            (
                LLMMessage(role="system", content=RESOLVE_TIMEZONE_SYSTEM_PROMPT),
                LLMMessage(role="user", content=text),
            ),
            ParsedTimezone,
        )
        if parsed.timezone is None:
            return None
        return _iana_name(parsed.timezone)

    async def suggest_translations(self, word: str) -> list[str]:
        result = await self._generate_structured(
            (
                LLMMessage(role="system", content=SUGGEST_TRANSLATIONS_SYSTEM_PROMPT),
                LLMMessage(role="user", content=word),
            ),
            WordTranslations,
        )
        translations: list[str] = []
        seen: set[str] = set()
        for item in result.translations:
            translation = item.strip()
            if not translation or translation in seen:
                continue
            seen.add(translation)
            translations.append(translation)
        if not translations:
            raise LLMResponseError("Модель не вернула переводы")
        return translations

    async def is_english_word(self, word: str) -> bool:
        result = await self._generate_structured(
            (
                LLMMessage(role="system", content=IS_ENGLISH_WORD_SYSTEM_PROMPT),
                LLMMessage(role="user", content=f"English candidate: {word}"),
            ),
            EnglishWord,
        )
        return result.is_english

    async def is_proper_name(self, word: str) -> bool:
        result = await self._generate_structured(
            (
                LLMMessage(role="system", content=IS_PROPER_NAME_SYSTEM_PROMPT),
                LLMMessage(role="user", content=f"English candidate: {word}"),
            ),
            ProperName,
        )
        return result.is_proper_name

    async def is_word_list(self, text: str) -> bool:
        result = await self._generate_structured(
            (
                LLMMessage(role="system", content=IS_WORD_LIST_SYSTEM_PROMPT),
                LLMMessage(role="user", content=text),
            ),
            WordList,
        )
        return result.is_word_list


def _answer_message(
    word: str,
    answer: str,
    translations: tuple[str, ...],
) -> str:
    lines = [f"English: {word}"]
    references = [item.strip() for item in translations if item.strip()]
    if references:
        lines.append(f"Reference translations: {'; '.join(references)}")
    lines.append(f"Answer: {answer}")
    return "\n".join(lines)


def _clock_time(hour: int | None, minute: int | None) -> time | None:
    if hour is None or minute is None:
        return None
    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        return None
    return time(hour=hour, minute=minute)


def _iana_name(text: str) -> str | None:
    candidate = " ".join(text.split())
    if not candidate:
        return None
    exact, folded = _iana_index()
    if candidate in exact:
        return candidate
    return folded.get(candidate.casefold())


@lru_cache(maxsize=1)
def _iana_index() -> tuple[frozenset[str], dict[str, str]]:
    zones = available_timezones()
    return frozenset(zones), {zone.casefold(): zone for zone in zones}
