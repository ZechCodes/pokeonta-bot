from __future__ import annotations
from pokeonta.logging import get_logger
from discord.ext import commands
from discord import Client
from typing import Any


class Cog(commands.Cog):
    def __init__(self, client: Client):
        self.client = client
        self.logger = get_logger(("pokeonta", self.__class__.__name__))

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.debug("Cog ready")
        await self.ready()

    async def ready(self):
        return

    @staticmethod
    def command(*args, **kwargs) -> Any:
        return commands.command(*args, **kwargs)

    @staticmethod
    def group(*args, **kwargs) -> commands.Group:
        return commands.group(*args, **kwargs)
