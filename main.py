import asyncio
from app import SpotifyChangeListener, LightController, config

import logging
logging.getLogger().setLevel(logging.INFO)


def main():
    async def _main():
        queue = asyncio.Queue()
        controller = LightController(queue, config.LED_IPS)
        listener = SpotifyChangeListener(queue, config.SPOTIFY_USERNAME)
        await asyncio.gather(listener.listen(), controller.consume())

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(_main())

if __name__ == '__main__':
    main()

