from pydantic import BaseModel


class TranslationVerdict(BaseModel):
    is_russian: bool
    is_correct: bool
    remarks: str = ""


class VerdictReview(BaseModel):
    verdict_holds: bool
    remarks: str = ""
