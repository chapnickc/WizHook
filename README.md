
# WizHook


Welcome! I'm glad you found the project. 

This codebase allows you to synchronize your Wiz connected light 
with the music you play on Spotify. 
To get started, you will need a few things:

* [Spotify Developer Account](https://developer.spotify.com/dashboard)
* [Python 3](https://docs.python-guide.org/starting/install3/osx/)
* Git (Optional, see below)
* MacOS / UNIX OS
* Patience (no link)

### Spotify Developer Account

Sign up for a free Spotify developer account here:

[developer.spotify.com/dashboard](https://developer.spotify.com/dashboard)

Once you have a Spotify developer account, navigate to the [dashboard](https://developer.spotify.com/dashboard)
and create a new application. The setup process should be straightforward, and at the end 
you obtain two specific credentials:

```
Client ID     xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
Client Secret xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Keep a note of these.

Lastly, edit the app settings. In the "Redirect URIs" add http://0.0.0.0:8888/.
More on this later.

### Python 3 

If you're using Mac OS, it comes with Python 2.7 out of the box.
But we want Python 3, because it's 2020 and Python 2 is no longer supported.
To install Python 3, follow the instructions [here](https://docs.python-guide.org/starting/install3/osx/).

### Git

If you don't have git installed, you can install it with homebrew.

```sh
brew install git
```
-------------------

## Getting Started

Get the source code:
```sh
$ git clone http://github.com/chapnickc/WizHook
$ cd WizHook
```

Install the dependencies
```sh
$ pip install spotipy pywizlight aiohttp
```

Edit `env.sh`, with *your* account credentials

```sh
export SPOTIPY_USERNAME="yourusername"
export SPOTIPY_CLIENT_ID="yourclientid"
export SPOTIPY_CLIENT_SECRET="yourclientsecret"
```

Edit app/config.py and enter the IP address of your wiz light:
```py
LED_IPS = [
    "192.168.0.22"
]
```

### Run the application

In Terminal.app

```sh
$ cd WizHook
$ . ./env.sh
$ python main.py
```

The first time you run the script you need to obtain credentials.
The workflow for this is a little funky. Running main.py should 
start your browser and redirect you to a URL.

Copy and paste the url from the browser into Terminal.app.

Profit!

Your light should start changing color with the 
active song. The default color is "International Orange".

To stop the script type Ctrl-C.

----------------------

Helpful:

[https://github.com/sbidy/wiz_light/blob/master/test.py](https://github.com/sbidy/wiz_light/blob/master/test.py)


