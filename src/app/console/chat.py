import asyncio

import typer

from app.core.container import get_context_container
from app.defs import UserIntent
from app.services.exceptions import PendingQuestionNotFoundError, UserVersionError
from app.telegram.command import TELEGRAM_COMMAND_DESCRIPTIONS
from app.telegram.texts import QUESTION_TEXT

STARTER_WORDS = (
    "apple",
    "journey",
    "to postpone",
    "nevertheless",
    "curious",
)
EXIT_COMMAND = "/exit"
ENTER_COMMAND_TEXT = "Сначала введите команду."

cli = typer.Typer()


@cli.command("chat")
def chat() -> None:
    asyncio.run(_run_chat())


async def _run_chat() -> None:
    async with get_context_container() as container:
        user = await container.user_service.get_default_user()
        if not await container.vocabulary_service.has_items(user.telegram_user_id):
            await container.vocabulary_service.add_items(
                user.telegram_user_id,
                STARTER_WORDS,
            )

        while True:
            user = await container.user_service.get_default_user()
            try:
                answer = typer.prompt(
                    "",
                    prompt_suffix="> ",
                    default="",
                    show_default=False,
                )
            except (EOFError, typer.Abort):
                break

            text = answer.strip()
            if text == EXIT_COMMAND:
                break

            service = container.user_reply_service
            try:
                if text.startswith("/"):
                    message = await service.handle_command(
                        user.telegram_user_id,
                        text[1:],
                        user.version,
                    )
                    shown = "" if message is None else message.text
                else:
                    match user.intent:
                        case UserIntent.SCHEDULE:
                            reply = await service.handle_schedule(
                                user.telegram_user_id,
                                user.version,
                                text,
                            )
                            shown = reply.text
                        case UserIntent.TIMEZONE:
                            reply = await service.handle_timezone(
                                user.telegram_user_id,
                                user.version,
                                text,
                            )
                            shown = reply.text
                        case UserIntent.ADD_WORDS:
                            reply = await service.handle_add_words(
                                user.telegram_user_id,
                                user.version,
                                text,
                            )
                            shown = reply.text
                        case UserIntent.ANSWER:
                            reply = await service.handle_answer(
                                user.telegram_user_id,
                                user.version,
                                text,
                            )
                            parts: list[str] = []
                            if reply.text:
                                parts.append(reply.text)
                            if reply.question is not None:
                                parts.append(
                                    QUESTION_TEXT.format(
                                        word=reply.question.word,
                                        text=reply.question.text,
                                    ),
                                )
                            shown = "\n\n".join(parts)
                        case _:
                            lines = [ENTER_COMMAND_TEXT]
                            for command, description in (
                                TELEGRAM_COMMAND_DESCRIPTIONS.items()
                            ):
                                lines.append(f"/{command} — {description}")
                            shown = "\n".join(lines)
            except (PendingQuestionNotFoundError, UserVersionError):
                continue

            if shown:
                typer.echo()
                typer.echo(shown)
                typer.echo()
