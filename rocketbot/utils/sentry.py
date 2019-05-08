import logging

import raven

_client = None
try:
    import bot_config
    if hasattr(bot_config, 'SENTRY_URL') and getattr(bot_config, 'SENTRY_URL') is not None:
        _client = raven.Client(getattr(bot_config, 'SENTRY_URL'))
except Exception:
    pass

if _client is None:
    logging.warning("SENTRY DISABLED!! Provide a SENTRY_URL in the bot_config to activate sentry logging")


def exception() -> None:
    if _client:
        _client.captureException()


def message(msg: str) -> None:
    if _client:
        _client.captureMessage(msg)
