import sys
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from app.core.container import get_context_container
from app.core.disposer import dispose
from app.defs import HOOK_PATH
from app.routes.hook import router as hook_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with get_context_container() as container:
        app.state.container = container
        try:
            await container.telegram_client.set_webhook(
                container.config.telegram_bot_url.rstrip("/") + HOOK_PATH
            )
            await container.telegram_client.set_commands()
            yield
        finally:
            try:
                await container.telegram_client.delete_webhook()
            finally:
                app.state.container = None
                await dispose()


app = FastAPI(lifespan=lifespan)
app.include_router(hook_router)


def main() -> None:
    host = sys.argv[1]
    port = int(sys.argv[2])
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
