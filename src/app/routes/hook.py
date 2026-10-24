import logging
import secrets
from pathlib import Path

from fastapi import APIRouter, Header, Request, Response

from app.core.container import Container
from app.core.logging import user_telegram_id
from app.defs import HOOK_PATH, UserIntent, MessageDirect
from app.events.tasks import (
    emit_add_words,
    emit_answer,
    emit_dont_know,
    emit_setup_schedule,
    emit_study,
    emit_telegram,
    emit_timezone,
    emit_translate,
)
from app.schemas import (
    AnswerCallbackQueryResponse,
    IncomingTelegramUpdate,
    SendMessageResponse,
    TelegramMethodResponse,
)
from app.telegram import TelegramCommand
from app.telegram.reply import WELCOME
from app.telegram.texts import ADD_WORDS_ACCEPTED_TEXT

_INCOMING_PATH = Path("telegram.txt")

logger = logging.getLogger("app.hook")

router = APIRouter()


@router.post(
    HOOK_PATH,
    response_model=AnswerCallbackQueryResponse | SendMessageResponse,
    response_model_exclude_none=True,
)
async def hook(
    update: IncomingTelegramUpdate,
    request: Request,
    secret_token: str = Header(default="", alias="X-Telegram-Bot-Api-Secret-Token"),
) -> Response | TelegramMethodResponse:
    expected = request.app.state.webhook_secret
    if not isinstance(expected, str) or not secrets.compare_digest(secret_token, expected):
        logger.warning("Отклонён запрос хука: неверный secret token")
        return Response(status_code=401)

    try:
        container: Container = request.app.state.container
        response: Response | TelegramMethodResponse
        if update.callback_query is not None:
            response = AnswerCallbackQueryResponse(
                callback_query_id=update.callback_query.query_id,
            )
        else:
            response = Response(status_code=200)
        
        text = update.text

        token = user_telegram_id.set(update.user_id)
        logger.info("Входящее сообщение %s: %s", update.update_id, text)
        await container.chat_message_service.add(update.user_id, MessageDirect.IN, text)

        accepted = await container.telegram_update_service.add_update(update.update_id)
        if accepted:
            async with container.transaction():
                created = await container.user_service.get_or_create(update.user_id)
                user = created.user
                if update.callback_query is not None:
                    command = text
                elif text.startswith("/"):
                    text = text[1:]
                    command = text
                else:
                    command = None
                if command == TelegramCommand.DONT_KNOW:
                    await container.event_service.publish(
                        emit_dont_know(user.telegram_user_id, user.version),
                    )
                elif command == TelegramCommand.STUDY:
                    await container.event_service.publish(
                        emit_study(user.telegram_user_id, user.version),
                    )
                elif command is not None:
                    message = await container.user_reply_service.handle_command(
                        user.telegram_user_id,
                        command,
                    )
                    if message is not None:
                        if update.callback_query is not None:
                            await container.event_service.publish(
                                emit_telegram(user.telegram_user_id, message),
                            )
                        else:
                            response = SendMessageResponse(
                                chat_id=user.telegram_user_id,
                                text=message.text,
                                reply_markup=message.reply_markup,
                            )
                            await container.chat_message_service.add(
                                user.telegram_user_id,
                                MessageDirect.OUT,
                                message.text,
                            )
                elif created.created:
                    await container.event_service.publish(
                        emit_telegram(user.telegram_user_id, WELCOME),
                    )
                else:
                    match user.intent:
                        case UserIntent.SCHEDULE:
                            await container.event_service.publish(
                                emit_setup_schedule(
                                    user.telegram_user_id,
                                    user.version,
                                    text,
                                ),
                            )
                        case UserIntent.TIMEZONE:
                            await container.event_service.publish(
                                emit_timezone(
                                    user.telegram_user_id,
                                    user.version,
                                    text,
                                ),
                            )
                        case UserIntent.ADD_WORDS:
                            response = SendMessageResponse(
                                chat_id=user.telegram_user_id,
                                text=ADD_WORDS_ACCEPTED_TEXT,
                            )
                            await container.chat_message_service.add(
                                user.telegram_user_id,
                                MessageDirect.OUT,
                                ADD_WORDS_ACCEPTED_TEXT,
                            )
                            await container.event_service.publish(
                                emit_add_words(
                                    user.telegram_user_id,
                                    user.version,
                                    text,
                                ),
                            )
                        case UserIntent.ANSWER:
                            await container.event_service.publish(
                                emit_answer(
                                    user.telegram_user_id,
                                    user.version,
                                    text,
                                ),
                            )
                        case UserIntent.UNKNOWN:
                            await container.event_service.publish(
                                emit_translate(
                                    user.telegram_user_id,
                                    user.version,
                                    text,
                                ),
                            )
        if isinstance(response, TelegramMethodResponse):
            logger.info(
                "Ответ 200 %s",
                response.model_dump(mode="json", exclude_none=True),
            )
        else:
            logger.info("Ответ %s", response.status_code)
        return response
    except Exception:
        logger.exception("Ошибка хука")
        raise
    finally:
        user_telegram_id.reset(token)
