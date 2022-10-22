from __future__ import annotations
from . import config
from .AnalysisHelper import AnalysisHelper
from .events import (
		Event,
		EventSongChanged,
		EventStop,
		EventAdjustStartTime,
		RawSpotifyResponse,
		Colors)
from pywizlight.bulb import wizlight, PilotBuilder
import asyncio
from typing import NoReturn, AsyncIterable, Callable
from bisect import bisect_left
import time
import logging
import random
import colorsys

def get_empty_colors(leds: int) -> Colors:
   return [(255, 90, 0)] * leds

async def _color_generator(leds: int, event_queue: asyncio.Queue[Event]) -> AsyncIterable[Colors]:
    get_current_colors = None
    start_time = 0
    event = EventStop()

    while True:
        while not event_queue.empty():
            event = event_queue.get_nowait()

        if isinstance(event, EventSongChanged):
            start_time = event.start_time
            helper = AnalysisHelper(event.analysis, leds)
            get_current_colors = helper.get_current_colors
        elif isinstance(event, EventAdjustStartTime):
            start_time = event.start_time
        elif isinstance(event, EventStop):
            get_current_colors = None

        if get_current_colors is None:
            yield get_empty_colors(leds)
        else:
            yield get_current_colors(time.time() - start_time)


class LightController:
    def __init__(self, event_queue: asyncio.Queue[Event], ip_list: list):
        self.queue = event_queue
        self.lights = [wizlight(ip_list[i]) for i in range(len(ip_list))]

    async def send_to_device(self, colors: Colors) -> None:
        if len(colors) != len(self.lights): return
        try:
            ops = [
                self.lights[i].turn_on(PilotBuilder(rgb=colors[i]))
				for i in range(len(self.lights))
			]
            await asyncio.gather(*ops)
        except Exception:
            logging.exception("Something went wrong with LightController")
            await asyncio.sleep(config.CONTROLLER_ERROR_DELAY)

    async def consume(self):
        while True:
            try:
                async for colors in _color_generator(len(self.lights), self.queue):
                    print('Color[0]=', colors[0])
                    await self.send_to_device(colors)
            except Exception:
                logging.exception("Something went wrong with LightController")
                await asyncio.sleep(config.CONTROLLER_ERROR_DELAY)

