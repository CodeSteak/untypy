import asyncio


async def some_coroutine_generator(x: int) -> str:
    await asyncio.sleep(0.0000001)
    yield "1"
    yield "2"
    yield "3"


async def some_coroutine(x: int) -> str:
    await asyncio.sleep(0.0000001)
    return str(x)


def some_generator() -> int
