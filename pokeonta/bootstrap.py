import pokeonta.config as config
import pokeonta.logging
import discord.ext.commands
import logging


def create_bot(logger) -> discord.ext.commands.Bot:
    bot_settings = pokeonta.config.scope_getter("bot")

    logger.debug(f"Creating bot with prefix '{bot_settings('prefix')}'")
    client = discord.ext.commands.Bot(
        command_prefix=bot_settings("prefix"),
        activity=discord.Activity(
            name=bot_settings("status"),
            type=discord.ActivityType.watching,
        ),
    )
    client.remove_command("help")
    return client


def load_cogs(client: discord.ext.commands.Bot, logger):
    logger.debug("Loading cogs")
    files = ("production" if pokeonta.config.get_setting("PRODUCTION_BOT") else "development",)
    for cog, settings in pokeonta.config.get_scope("cogs", filenames=files):
        enabled = settings if isinstance(settings, bool) else settings.get("enabled", True)
        path = (
            f"pokeonta.cogs.{cog}"
            if isinstance(settings, bool) or not settings.get("from")
            else settings.get("from")
        )
        if enabled:
            logger.debug(f"LOADED - {path}")
            client.load_extension(path)
        else:
            logger.debug(f"DISABLED - {path}")


def run(client, logger):
    logger.debug("Looking for token")

    token = _get_token()
    if not token or len(token.strip()) != 59:
        message = (
            f"Got token: {repr(token)}\n"
            f"Please set a token in your environment as DISCORD_TOKEN or in your developement.yaml file under 'bot' "
            f"with the key 'token'."
        )
        raise InvalidToken(message)

    logger.debug("Starting the bot")
    client.run(token)
    logger.debug("Bot has exited")


def setup_logger():
    """ Configures how logs are printed and sets the log level. """
    log_settings = config.scope_getter("logging")

    log_format = log_settings("format")
    date_format = log_settings("date_format")

    levels = {
        "*": logging.DEBUG,
        "all": logging.DEBUG,
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warn": logging.WARN,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
    }
    level = levels.get(
        log_settings("level", env_name="LOGGING_LEVEL", default="").casefold(),
        logging.INFO
    )

    logging.basicConfig(
        format=log_format,
        datefmt=date_format,
        level=levels.get(log_settings("global_level", default="").casefold(), logging.ERROR)
    )

    logger = pokeonta.logging.get_logger()
    logger.setLevel(level)

    for name, _level in log_settings("loggers", default={}).items():
        _level = levels.get(_level.casefold(), logging.ERROR)
        logging.getLogger(name).setLevel(_level)

    return logger


def _get_token():
    token = pokeonta.config.get_setting("token", scope="bot", env_name="DISCORD_TOKEN", default="")
    return token.strip()


class InvalidToken(Exception):
    ...
