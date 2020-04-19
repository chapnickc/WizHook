import asyncio
from app import SpotifyChangeListener, LightController

import logging
logging.getLogger().setLevel(logging.INFO)

def main():
    queue = asyncio.Queue()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.gather(
        SpotifyChangeListener(queue),
        LightController(queue)
    ))

if __name__ == '__main__':
    main()

