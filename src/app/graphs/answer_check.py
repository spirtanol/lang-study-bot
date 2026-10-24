from dataclasses import dataclass
from typing import Protocol, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.schemas.llm import TranslationVerdict, VerdictReview


class TranslationChecks(Protocol):
    async def check_translation(
        self,
        word: str,
        answer: str,
        translations: tuple[str, ...] = (),
    ) -> TranslationVerdict: ...

    async def review_translation_verdict(
        self,
        word: str,
        answer: str,
        verdict: TranslationVerdict,
        translations: tuple[str, ...] = (),
    ) -> VerdictReview: ...

    async def correct_translations(
        self,
        word: str,
        translations: tuple[str, ...] = (),
    ) -> list[str]: ...


class AnswerCheckState(TypedDict):
    word: str
    answer: str
    translations: list[str]
    is_russian: bool
    is_correct: bool
    remarks: str
    accepted: bool


@dataclass(frozen=True, slots=True)
class AnswerCheckVerdict:
    accepted: bool
    remarks: str


class AnswerCheckGraph:
    def __init__(self, language_model: TranslationChecks):
        self._graph = _compile(language_model)

    async def run(
        self,
        word: str,
        answer: str,
        translations: tuple[str, ...],
    ) -> AnswerCheckVerdict:
        state = await self._graph.ainvoke(
            AnswerCheckState(
                word=word,
                answer=answer,
                translations=list(translations),
                is_russian=False,
                is_correct=False,
                remarks="",
                accepted=False,
            )
        )
        return AnswerCheckVerdict(
            accepted=state["accepted"],
            remarks=state["remarks"],
        )


def _compile(language_model: TranslationChecks) -> CompiledStateGraph:
    graph = StateGraph(AnswerCheckState)
    graph.add_node("check", _check(language_model))
    graph.add_node("review", _review(language_model))
    graph.add_node("translations", _translations(language_model))
    graph.add_edge(START, "check")
    graph.add_conditional_edges("check", _route_after_check)
    graph.add_conditional_edges("review", _route_after_review)
    graph.add_edge("translations", END)
    return graph.compile()


def _route_after_check(state: AnswerCheckState) -> str:
    if state["is_russian"] and state["is_correct"]:
        return "review"
    return "translations"


def _route_after_review(state: AnswerCheckState) -> str:
    if state["accepted"]:
        return END
    return "translations"


def _check(language_model: TranslationChecks):
    async def node(state: AnswerCheckState) -> dict[str, bool | str]:
        verdict = await language_model.check_translation(
            state["word"],
            state["answer"],
            tuple(state["translations"]),
        )
        return {
            "is_russian": verdict.is_russian,
            "is_correct": verdict.is_correct,
            "remarks": verdict.remarks,
        }

    return node


def _review(language_model: TranslationChecks):
    async def node(state: AnswerCheckState) -> dict[str, bool | str]:
        review = await language_model.review_translation_verdict(
            state["word"],
            state["answer"],
            TranslationVerdict(
                is_russian=state["is_russian"],
                is_correct=state["is_correct"],
                remarks=state["remarks"],
            ),
            tuple(state["translations"]),
        )
        if review.verdict_holds:
            return {"accepted": True, "remarks": ""}
        return {"accepted": False}

    return node


def _translations(language_model: TranslationChecks):
    async def node(state: AnswerCheckState) -> dict[str, str]:
        items = await language_model.correct_translations(
            state["word"],
            tuple(state["translations"]),
        )
        answer = ", ".join(items)
        remark = state["remarks"].strip()
        if remark:
            return {"remarks": f"{remark}\n{answer}"}
        return {"remarks": answer}

    return node
