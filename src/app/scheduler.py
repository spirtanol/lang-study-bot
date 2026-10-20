import asyncio
import signal

from app.core.container import get_context_container
from app.core.disposer import dispose
from app.core.logging import init_logging

TICK_SECONDS = 1


def main() -> None:
    init_logging()
    asyncio.run(_run())


async def _run() -> None:
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)

    async with get_context_container() as container:
        try:
            while not stop.is_set():
                await container.scheduler_service.run()
                try:
                    await asyncio.wait_for(stop.wait(), timeout=TICK_SECONDS)
                except TimeoutError:
                    pass
        finally:
            await dispose()


if __name__ == "__main__":
    main()
