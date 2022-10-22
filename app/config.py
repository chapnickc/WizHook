import os

API_CURRENT_PLAYING = 'https://api.spotify.com/v1/me/player/currently-playing'
API_AUDIO_ANALYSIS = 'https://api.spotify.com/v1/audio-analysis/'
SPOTIFY_SCOPE = 'user-read-currently-playing,user-read-playback-state'
SPOTIFY_CHANGES_LISTENER_DEALY = 1
SPOTIFY_CHANGES_LISTENER_FAILURE_DELAY = 1
SPOTIFY_USERNAME=os.getenv('SPOTIPY_USERNAME')

# Events listener, device controller
CONTROLLER_ERROR_DELAY = 1

LED_IPS = [
    "192.168.0.17",
    #"192.168.0.19",
]

SCALE=(255, 255, 255)

LED_COUNT = len(LED_IPS)
