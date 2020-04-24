import os

API_CURRENT_PLAYING = 'https://api.spotify.com/v1/me/player/currently-playing'
API_AUDIO_ANALYSIS = 'https://api.spotify.com/v1/audio-analysis/'
SPOTIFY_SCOPE = 'user-read-currently-playing,user-read-playback-state'
SPOTIFY_CHANGES_LISTENER_DEALY = 1
SPOTIFY_CHANGES_LISTENER_FAILURE_DELAY = 1
SPOTIFY_USERNAME=os.getenv('SPOTIPY_USERNAME')

LED_IPS = [
    "192.168.0.17",
    "192.168.0.19",
]
# LED_IPS = ["192.168.0.17", "192.168.0.19"]
LED_COUNT = len(LED_IPS)

# Light colors selector, spooky, more details in the notebook
# SCALE = (255, 255, 255)
SCALE = (255, 225, 255)



# Events listener, device controller
CONTROLLER_TICK = 0.4
CONTROLLER_ERROR_DELAY = 1


BASE_LIGHTNESS=0.7
LOUDNESS_MULTIPLIER = 1.3



