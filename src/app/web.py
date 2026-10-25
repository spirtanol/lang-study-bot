import logging
import secrets
import sys
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError

from app.core.container import get_context_container
from app.core.disposer import dispose
from app.core.logging import logging_dict
from app.defs import HOOK_PATH
from app.routes.hook import router as hook_router

logger = logging.getLogger("app.web")


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with get_context_container() as container:
        app.state.container = container
        app.state.webhook_secret = secrets.token_urlsafe(32)
        try:
            await container.telegram_client.set_webhook(
                container.config.telegram_bot_url.rstrip("/") + HOOK_PATH,
                app.state.webhook_secret,
            )
            await container.telegram_client.set_commands()
            yield
        finally:
            try:
                await container.telegram_client.delete_webhook()
            finally:
                app.state.container = None
                app.state.webhook_secret = None
                await dispose()


app = FastAPI(lifespan=lifespan)
app.include_router(hook_router)


@app.exception_handler(RequestValidationError)
async def log_invalid_request(request: Request, exc: RequestValidationError):
    logger.warning(
        "Невалидный запрос %s: %s; тело: %s",
        request.url.path,
        exc.errors(),
        exc.body,
    )
    return Response(status_code=200)


def main() -> None:
    host = sys.argv[1]
    port = int(sys.argv[2])
    uvicorn.run(app, host=host, port=port, log_config=logging_dict())


if __name__ == "__main__":
    main()
