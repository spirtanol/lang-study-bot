from typing import Callable


_to_dispose = []

def reg_to_dispose(dispose_func: Callable):
    global _to_dispose

    _to_dispose.append(dispose_func)

async def dispose():
    global _to_dispose

    for func in _to_dispose:
        await func()