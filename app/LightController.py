from __future__ import annotations
from . import config
from .events import (
        Event,
        EventSongChanged,
        EventStop,
        EventAdjustStartTime,
        RawSpotifyResponse,
        Colors
)
from pywizlight.bulb import wizlight, PilotBuilder
import asyncio
from typing import NoReturn, AsyncIterable, Callable
from bisect import bisect_left
import time
import logging
import random


def _normalize(pv: float) -> float:
    if pv < 0:
        return 0.
    elif pv > 255:
        return 255.
    else:
        return pv

def _scale_pixel(p):
    return (int(_normalize(p[0]) * config.SCALE[0] / 255),
            int(_normalize(p[1]) * config.SCALE[1] / 255),
            int(_normalize(p[2]) * config.SCALE[2] / 255))

def get_empty_colors(leds: int) -> Colors:
    return [(255, 90, 0)] * leds

def make_get_current_colors(analysis: RawSpotifyResponse, leds: int) -> Callable[[float], Colors]:
    def make_get_current(name):
        keys = [x['start'] for x in analysis[name]]
        key_to_x = {x['start']: x for x in analysis[name]}
        return lambda t: key_to_x[keys[bisect_left(keys, t) - 1]]

    get_current_segment = make_get_current('segments')
    get_current_section = make_get_current('sections')
    get_current_beat = make_get_current('beats')

    def make_scale(name):
        xs = [x[name] for x in analysis['sections']]
        min_xs = min(xs)
        max_xs = max(xs)
        return lambda x: (x - min_xs) / (max_xs - min_xs)

    scale_loudness = make_scale('loudness')
    scale_tempo = make_scale('tempo')

    def get_current_colors(t):
        segment = get_current_segment(t)
        section = get_current_section(t)
        beat = get_current_beat(t)

        beat_color = config.BEAT_MULTIPLIER * (t - beat['start'] + beat['duration']) / beat['duration']
        tempo_color = config.TEMPO_MULTIPLIER * scale_tempo(section['tempo'])
        pitch_colors = [config.PITCH_MULITPLIER * p for p in segment['pitches']]

        loudness_multiplier = 1 + config.LOUDNESS_MULTIPLIER * scale_loudness(section['loudness'])

        colors = (
            (beat_color * loudness_multiplier,
            tempo_color * loudness_multiplier,
            pitch_colors[0] * loudness_multiplier)
            # pitch_colors[n % len(pitch_colors)] * loudness_multiplier)
            for n in range(leds)
        )

        logging.info(f"mode={section['mode']}")
        if section['mode'] == 0:
            order = (0, 1, 2)
        elif section['mode'] == 1:
            order = (2, 1, 0)
        else:
            order = (1, 2, 0)

        ordered_colors = ((color[order[0]], color[order[1]], color[order[2]]) for color in colors)

        return [_scale_pixel(color) for color in ordered_colors]

    return get_current_colors



async def _events_to_colors(leds: int, event_queue: asyncio.Queue[Event]) -> AsyncIterable[Colors]:
    get_current_colors = None
    start_time = 0
    event = EventStop()
    while True:
        #await asyncio.sleep(config.CONTROLLER_TICK)

        while not event_queue.empty():
            event = event_queue.get_nowait()

        if isinstance(event, EventSongChanged):
            start_time = event.start_time
            get_current_colors = make_get_current_colors(event.analysis, leds)
        elif isinstance(event, EventAdjustStartTime):
            start_time = event.start_time
        elif isinstance(event, EventStop):
            get_current_colors = None

        if get_current_colors is None:
            yield get_empty_colors(leds)
        else:
            yield get_current_colors(time.time() - start_time)



async def send_to_device(colors: Colors) -> None:
    if len(colors) != len(config.LED_IPS): return
    for i in range(len(config.LED_IPS)):
        logging.info(f'IP={config.LED_IPS[i]} Color={colors[i]}')
    ops = [wizlight(config.LED_IPS[i]).turn_on(PilotBuilder(rgb=colors[i])) for i in range(len(config.LED_IPS))]
    loop = asyncio.get_event_loop()
    await asyncio.gather(*ops, loop=loop)

async def LightController(event_queue: asyncio.Queue[Event]) -> NoReturn:
    while True:
        try:
            leds = len(config.LED_IPS)
            async for colors in _events_to_colors(leds, event_queue):
                await send_to_device(colors)
            await asyncio.sleep(config.CONTROLLER_TICK)
        except Exception:
            logging.exception("Something went wrong with lights_controller")
            await asyncio.sleep(config.CONTROLLER_ERROR_DELAY)


