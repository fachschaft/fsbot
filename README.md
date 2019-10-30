# Rocketbot

[![Build Status](https://travis-ci.org/fachschaft/fsbot.svg?branch=master)](https://travis-ci.org/fachschaft/fsbot) [![codecov](https://codecov.io/gh/fachschaft/fsbot/branch/master/graph/badge.svg)](https://codecov.io/gh/fachschaft/fsbot)

This repository contains a [Rocket.Chat](https://github.com/RocketChat/Rocket.Chat) bot based on the [realtime api](https://rocket.chat/docs/developer-guides/realtime-api/).

# Usage

An example on how to use this bot can be found in `main.py`.

The core of this bot framework is the `master.py` which handles a collection of bots. Bots themselves can be individually assembled by the various mixin classes in:
- `bots/accesscontrol.py`: Allow/disallow rooms/roomtypes
- `bots/messagefilter.py`: Filter messages by user, by mentions, ...
- `bots/messagehandler.py`: Take actions by incoming messages

# Deployment
1. Clone this repo.
2. Rename `bot_config.py.dist.py` to `bot_config.py` and adjust the config values to your environment.
3. Start the bot:
    - Via python:
    ```
    pip install -r requirements.txt
    python3 main.py
    ```
    - Via docker:
    ```
    docker build --tag=rocketbot .
    docker run -v ${PWD}:/bot rocketbot
    ```
    - Via docker-compose:
    ```
    bot:
      build: ./rocketbot
      volumes:
        - ./rocketbot:/bot
      command: python3 main.py
    ```
