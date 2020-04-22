from __future__ import annotations
from . import config
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
import math


def _normalize(pv: float) -> float:
	if pv < 0:
		return 1.
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
    get_current_bar = make_get_current('bars')

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
        bar = get_current_bar(t)

        bar_color = (t - bar['start'] + bar['duration']) / bar['duration']
        beat_color = (t - beat['start'] + beat['duration']) / beat['duration']
        tempo_color = scale_tempo(section['tempo'])
        pitch_colors = [p for p in segment['pitches']]
        timbre_colors = [p for p in segment['timbre']]

        loudness =  config.LOUDNESS_MULTIPLIER * scale_loudness(section['loudness'])
        # print(segment)

        colors = []
        for n in range(leds):
            s, v = 1 ,1
            if config.MODE == 1:
                h = 0.75*tempo_color
            elif config.MODE == 2:
                h = 0.75*tempo_color + -0.2*math.log(bar_color%1, 10);
            elif config.MODE == 3:
                h = 0.75*tempo_color + -0.03*math.log(bar_color%1, 10);
            else:
                h = 0.75*tempo_color + 0.25*pitch_colors[0] + 0.25*(bar_color%1);

            if not 0 < h <= 1: h = 1
            if not 0 < s <= 1: s = 1
            if not 0 < v <= 1: v = 1
            rgb = colorsys.hsv_to_rgb(h, s, v)
            colors.append(_scale_pixel([255*p for p in rgb]))

        #    tempo_color * loudness_multiplier, #    pitch_colors[0] * loudness_multiplier) #    for n in range(leds))
        #if section['mode'] == 0 or True:
        order = (0, 1, 2)
        #elif section['mode'] == 1:
        #    # order = (2, 0, 1)
        #    order = (2, 1, 1)
        #else:
        #    order = (2, 1, 0)

        ordered_colors = ((color[order[0]], color[order[1]], color[order[2]]) for color in colors)
        ret = [_scale_pixel(color) for color in ordered_colors]
        for i in range(len(config.LED_IPS)): logging.info(f'IP={config.LED_IPS[i]} mode={section["mode"]} Color={ret[i]}')
        return  ret

    return get_current_colors


async def _events_to_colors(leds: int, event_queue: asyncio.Queue[Event]) -> AsyncIterable[Colors]:
    get_current_colors = None
    start_time = 0
    event = EventStop()

    while True:
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


class LightController:
    def __init__(self, event_queue: asyncio.Queue[Event]):
        self.queue = event_queue

    async def send_to_device(self, colors: Colors) -> None:
        if len(colors) != len(config.LED_IPS): return
        try:
            ops = [wizlight(config.LED_IPS[i]).turn_on(PilotBuilder(rgb=colors[i])) for i in range(len(config.LED_IPS))]
            loop = asyncio.get_event_loop()
            await asyncio.gather(*ops, loop=loop)
        except Exception:
            logging.exception("Something went wrong with LightController")
            await asyncio.sleep(config.CONTROLLER_ERROR_DELAY)

    async def consume(self):
        while True:
            try:
                async for colors in _events_to_colors(len(config.LED_IPS), self.queue):
                    await self.send_to_device(colors)
            except Exception:
                logging.exception("Something went wrong with LightController")
                await asyncio.sleep(config.CONTROLLER_ERROR_DELAY)

