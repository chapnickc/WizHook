from .events import (
        RawSpotifyResponse,
        EventSongChanged,
        EventStop,
        EventAdjustStartTime,
        Event
)
from . import config
import asyncio
import aiohttp
import time
import logging
import spotipy

from typing import Union, Dict, Any, NoReturn, AsyncIterable, List, Tuple, Callable


API_CURRENT_PLAYING = 'https://api.spotify.com/v1/me/player/currently-playing'
async def _get_current_playing(session: aiohttp.ClientSession) -> RawSpotifyResponse:
    async with session.get(API_CURRENT_PLAYING) as response:
        return await response.json()

async def _get_audio_analysis(session: aiohttp.ClientSession, id: str) -> RawSpotifyResponse:
    async with session.get(config.API_AUDIO_ANALYSIS + id) as response:
        return await response.json()

def _get_start_time(current_playing, request_time: float) -> float:
    # spotify timestamp appears to be incorrect https://github.com/spotify/web-api/issues/640
    return (request_time + time.time()) / 2 - current_playing['progress_ms'] / 1000

async def _listen_for_events(session) -> AsyncIterable[Event]:
    current_id = None
    while True:
        request_time = time.time()
        current = await _get_current_playing(session)
        if not current['is_playing']:
            current_id = None
            logging.info(f'Stop Event')
            yield EventStop()
        elif current['item']['id'] != current_id:
            current_id = current['item']['id']
            analysis = await _get_audio_analysis(session, current_id)
            logging.info(f'Retrieved analysis for time={request_time}, id={current_id}')
            yield EventSongChanged(analysis, _get_start_time(current, request_time))
        else:
            logging.info(f'Adjusting start time {request_time}')
            yield EventAdjustStartTime(_get_start_time(current, request_time))
        await asyncio.sleep(config.SPOTIFY_CHANGES_LISTENER_DEALY)


async def SpotifyChangeListener(event_queue):
    while True:
        sp = spotipy.Spotify(auth_manager=spotipy.SpotifyOAuth(
                    username=config.SPOTIFY_USERNAME,
                    scope=config.SPOTIFY_SCOPE
                ))
        token = sp.auth_manager.get_access_token(as_dict=False)
        headers = {'Authorization': f'Bearer {token}'}
        async with aiohttp.ClientSession(headers=headers) as session:
            try:
                async for event in _listen_for_events(session):
                    await event_queue.put(event)
            except Exception as e:
                logging.exception(f'{e}')
                await asyncio.sleep(config.SPOTIFY_CHANGES_LISTENER_FAILURE_DELAY)

