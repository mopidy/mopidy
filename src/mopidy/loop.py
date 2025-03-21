import asyncio


def get_or_create_loop() -> asyncio.AbstractEventLoop:
    """
    Get the current event loop or create a new one if there is no current event loop.
    """

    try:
        return asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop


def stop_loop(loop: asyncio.AbstractEventLoop) -> None:
    """
    Stop the event loop and wait for it to finish.
    """

    try:
        loop.call_soon_threadsafe(loop.stop)
    except RuntimeError:
        pass

    try:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.run_until_complete(loop.shutdown_default_executor())
    except (AttributeError, NotImplementedError):
        pass

    try:
        loop.close()
    except RuntimeError:
        pass
