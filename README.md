# Rocketbot

This repository contains a [Rocket.Chat](https://github.com/RocketChat/Rocket.Chat) bot based on the [realtime api](https://rocket.chat/docs/developer-guides/realtime-api/).

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
