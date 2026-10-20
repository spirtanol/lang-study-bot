import re
from dataclasses import dataclass
from typing import Protocol, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.llm import LLMError, LLMUnavailableError


class WordChecks(Protocol):
    async def is_english_word(self, word: str) -> bool: ...

    async def is_proper_name(self, word: str) -> bool: ...

    async def suggest_translations(self, word: str) -> list[str]: ...


_CYRILLIC = re.compile(r"[\u0400-\u04FF]")
_ARTICLES = frozenset({"a", "an", "the"})
_TO_BE = frozenset(
    {"be", "am", "is", "are", "was", "were", "been", "being", "to be"}
)
_RUSSIAN_REASON = "на русском"
_NOT_ENGLISH_REASON = "не английское"
_ARTICLE_REASON = "артикль"
_TO_BE_REASON = "глагол to be"
_PROPER_NAME_REASON = "имя собственное"
_NO_TRANSLATION_REASON = "нет перевода"


class AddWordState(TypedDict):
    word: str
    accept: bool
    reason: str
    translations: list[str]


@dataclass(frozen=True, slots=True)
class AddWordVerdict:
    accept: bool
    reason: str
    translations: tuple[str, ...]


class AddWordsGraph:
    def __init__(self, language_model: WordChecks):
        self._graph = _compile(language_model)

    async def run(self, word: str) -> AddWordVerdict:
        state = await self._graph.ainvoke(
            AddWordState(
                word=word,
                accept=True,
                reason="",
                translations=[],
            )
        )
        return AddWordVerdict(
            accept=state["accept"],
            reason=state["reason"],
            translations=tuple(state["translations"]),
        )


def _compile(language_model: WordChecks) -> CompiledStateGraph:
    graph = StateGraph(AddWordState)
    graph.add_node("english", _english(language_model))
    graph.add_node("article", _article)
    graph.add_node("to_be", _to_be)
    graph.add_node("proper_name", _proper_name(language_model))
    graph.add_node("translation", _translation(language_model))
    graph.add_edge(START, "english")
    graph.add_conditional_edges("english", _continue("article"))
    graph.add_conditional_edges("article", _continue("to_be"))
    graph.add_conditional_edges("to_be", _continue("proper_name"))
    graph.add_conditional_edges("proper_name", _continue("translation"))
    graph.add_edge("translation", END)
    return graph.compile()


def _continue(next_node: str):
    def route(state: AddWordState) -> str:
        if state["accept"]:
            return next_node
        return END

    return route


def _english(language_model: WordChecks):
    async def node(state: AddWordState) -> dict[str, bool | str]:
        word = state["word"]
        if _CYRILLIC.search(word):
            return {"accept": False, "reason": _RUSSIAN_REASON}
        if not await language_model.is_english_word(word):
            return {"accept": False, "reason": _NOT_ENGLISH_REASON}
        return {"accept": True}

    return node


async def _article(state: AddWordState) -> dict[str, bool | str]:
    if state["word"].lower() in _ARTICLES:
        return {"accept": False, "reason": _ARTICLE_REASON}
    return {"accept": True}


async def _to_be(state: AddWordState) -> dict[str, bool | str]:
    if state["word"].lower() in _TO_BE:
        return {"accept": False, "reason": _TO_BE_REASON}
    return {"accept": True}


def _proper_name(language_model: WordChecks):
    async def node(state: AddWordState) -> dict[str, bool | str]:
        if await language_model.is_proper_name(state["word"]):
            return {"accept": False, "reason": _PROPER_NAME_REASON}
        return {"accept": True}

    return node


def _translation(language_model: WordChecks):
    async def node(state: AddWordState) -> dict[str, bool | str | list[str]]:
        try:
            translations = await language_model.suggest_translations(state["word"])
        except LLMUnavailableError:
            raise
        except LLMError:
            return {
                "accept": False,
                "reason": _NO_TRANSLATION_REASON,
                "translations": [],
            }
        return {"accept": True, "translations": translations}

    return node
