import asyncio
from app import SpotifyChangeListener, LightController

import logging
logging.getLogger().setLevel(logging.INFO)


def main():
    async def _main():
        queue = asyncio.Queue()
        controller = LightController(queue)
        listener = SpotifyChangeListener(queue)
        await asyncio.gather(listener.listen(), controller.consume())

    loop = asyncio.get_event_loop()
    loop.run_until_complete(_main())

if __name__ == '__main__':
    main()

