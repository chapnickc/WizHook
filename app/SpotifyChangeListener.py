from .events import (
        RawSpotifyResponse,
        EventSongChanged,
        EventStop,
        EventAdjustStartTime,
        Event)
from . import config
import asyncio
import aiohttp
import time
import logging
import spotipy
from typing import Union, Dict, Any, NoReturn, AsyncIterable, List, Tuple, Callable


class SpotifyChangeListener:
    def __init__(self, event_queue):
        self.queue = event_queue
        self.headers = None
        self.session = None

    async def get_new_token(self):
        sp = spotipy.Spotify(
                auth_manager=spotipy.SpotifyOAuth(
                    username=config.SPOTIFY_USERNAME,
                    scope=config.SPOTIFY_SCOPE))
        token = sp.auth_manager.get_access_token(as_dict=False)
        self.headers = {'Authorization': f'Bearer {token}'}
        self.sp = sp

    async def _get_current_playing(self, session: aiohttp.ClientSession) -> RawSpotifyResponse:
        async with session.get(config.API_CURRENT_PLAYING) as response:
            return await response.json()

    async def _get_audio_analysis(self, session: aiohttp.ClientSession, id: str) -> RawSpotifyResponse:
        async with session.get(config.API_AUDIO_ANALYSIS + id) as response:
            return await response.json()

    def _get_start_time(self, current_playing, request_time: float) -> float:
        # spotify timestamp appears to be incorrect https://github.com/spotify/web-api/issues/640
        return (request_time + time.time()) / 2 - (current_playing['progress_ms'] / 1000)  + config.OFFSET

    async def _listen_for_events(self, session) -> AsyncIterable[Event]:
        current_id = None
        while True:
            request_time = time.time()
            current = await self._get_current_playing(session)
            if not current['is_playing']:
                current_id = None
                yield EventStop()
            elif current['item']['id'] != current_id:
                current_id = current['item']['id']
                analysis = await self._get_audio_analysis(session, current_id)
                yield EventSongChanged(analysis, self._get_start_time(current, request_time))
            else:
                yield EventAdjustStartTime(self._get_start_time(current, request_time))

            await asyncio.sleep(config.SPOTIFY_CHANGES_LISTENER_DEALY)

    async def listen(self):
        while True:
            await self.get_new_token()
            async with aiohttp.ClientSession(headers=self.headers) as session:
                try:
                    async for event in self._listen_for_events(session):
                        await self.queue.put(event)
                except Exception as e:
                    logging.exception(f'{e}')
                    await self.get_new_token()
                    await asyncio.sleep(config.SPOTIFY_CHANGES_LISTENER_FAILURE_DELAY)

