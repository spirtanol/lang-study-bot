import asyncio
import logging
import signal

from app.core.container import get_context_container
from app.core.disposer import dispose

TICK_SECONDS = 1

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(name)s: %(message)s",
)


def main() -> None:
    asyncio.run(_run())


async def _run() -> None:
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)

    async with get_context_container() as container:
        try:
            while not stop.is_set():
                await container.scheduler_service.dispatch_due()
                try:
                    await asyncio.wait_for(stop.wait(), timeout=TICK_SECONDS)
                except TimeoutError:
                    pass
        finally:
            await dispose()


if __name__ == "__main__":
    main()
