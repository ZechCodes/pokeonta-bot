from __future__ import annotations
from pokeonta.cog import Cog
from dataclasses import dataclass
from typing import Dict, List
import asyncio
import datetime
import discord


class GoFestCog(Cog):
    def __init__(self, client):
        super().__init__(client)
        self.hourly_features = [
            Habitat(
                name="Battle",
                pokemon={
                    "Machop": True,
                    "Alolan Grimer": True,
                    "Dratini": True,
                    "Sneasel": True,
                    "Skarmory": True,
                    "Slakoth": True,
                    "Sableye": True,
                    "Meditite": True,
                    "Swablu": True,
                    "Zangoose": True,
                    "Seviper": True,
                    "Gible": True,
                    "Croagunk": True,
                    "Stunfisk": False,
                    "**Durant**": True,
                },
                times=[]
            ),
            Habitat(
                name="Friendship",
                pokemon={
                    "Pikachu": True,
                    "Clefairy": True,
                    "Jigglypuff": True,
                    "Chansey": True,
                    "Eevee": True,
                    "Snorlax": False,
                    "Togetic": False,
                    "Marill": True,
                    "Sudowoodo": True,
                    "Wobbuffet": True,
                    "Mantine": False,
                    "Roselia": True,
                    "Feebas": True,
                    "Chimecho": False,
                    "**Woobat**": True
                },
                times=[13]
            ),
            Habitat(
                name="Fire",
                pokemon={
                    "Charmander": True,
                    "Charizard": False,
                    "Vulpix": False,
                    "Ponyta": True,
                    "Alolan Marowak": True,
                    "Magmar": True,
                    "Flareon": False,
                    "Houndour": True,
                    "Torchic": True,
                    "Numel": False,
                    "Tepig": False,
                    "Darumaka": False,
                    "Litwick": False,
                    "**Heatmor**": True
                },
                times=[11]
            ),
            Habitat(
                name="Water",
                pokemon={
                    "Squirtle": True,
                    "Blastoise": False,
                    "Poliwag": True,
                    "Tentacool": True,
                    "Slowpoke": False,
                    "Magikarp": True,
                    "Chinchou": True,
                    "**Qwilfish**": True,
                    "Mudkip": True,
                    "Carvanha": True,
                    "Clamperl": True,
                    "Oshawott": True,
                    "Tympole": False,
                    "Alomomola": False
                },
                times=[12]
            ),
            Habitat(
                name="Grass",
                pokemon={
                    "Bulbasaur": True,
                    "Venusaur": False,
                    "Oddish": True,
                    "Exeggcute": True,
                    "Alolan Exeggcutor": True,
                    "**Tangela**": True,
                    "Sunkern": True,
                    "Treecko": True,
                    "Seedot": True,
                    "Cherrim": False,
                    "Snover": True,
                    "Leafeon": False,
                    "Snivy": False,
                    "Foongus": False,
                    "Ferroseed": False
                },
                times=[]
            )
        ]

    @Cog.command()
    async def habitat(self, ctx):
        now = datetime.datetime.utcnow() - datetime.timedelta(hours=4)
        await self.send_habitat_change(now.hour, current=True)

    async def ready(self):
        if datetime.datetime.utcnow() - datetime.timedelta(hours=4) < datetime.datetime(2020, 7, 25, 20, 0, 0, 0):
            self.logger.debug("Scheduling habitat change")
            asyncio.get_event_loop().create_task(self.schedule_habitat_change())
        elif datetime.datetime.utcnow() - datetime.timedelta(hours=4) < datetime.datetime(2020, 8, 16, 20, 0, 0, 0):
            self.logger.debug("Scheduling make up habitat change")
            asyncio.get_event_loop().create_task(self.schedule_habitat_change())

    async def schedule_habitat_change(self):
        now = datetime.datetime.utcnow() - datetime.timedelta(hours=4)
        next_change = now.replace(hour=now.hour + 1, minute=0, second=0, microsecond=0)
        self.logger.debug(f"Next habitat change in {(next_change - now).seconds} for hour {now.hour + 1}")
        await asyncio.sleep((next_change - now).seconds)

        await self.send_habitat_change(now.hour + 1)
        if now + datetime.timedelta(hours=2) < datetime.datetime(2020, 8, 16, 20, 0, 0, 0):
            await asyncio.sleep(60)
            asyncio.get_event_loop().create_task(self.schedule_habitat_change())

    async def send_habitat_change(self, hour: int, current: bool = False):
        self.logger.debug(f"Looking for habitat in hour {hour}")
        for habitat in self.hourly_features:
            if hour in habitat.times:
                await self.send_habitat_message(habitat, current)
                break

    async def send_habitat_message(self, habitat: Habitat, current: bool = False):
        guild = self.client.get_guild(340162408498593793)
        channel: discord.TextChannel = discord.utils.get(guild.channels, name="go-fest-2020")
        embed = (
            discord.Embed(
                title=f"We're currently in the {habitat.name} habitat" if current else f"We're now in the {habitat.name} Habitat!!!"
            )
            .add_field(
                name="Featured Shinies!!!",
                value=", ".join(
                    filter(lambda pokemon: habitat.pokemon[pokemon], habitat.pokemon)
                ),
                inline=False
            )
        )
        other = list(filter(lambda pokemon: not habitat.pokemon[pokemon], habitat.pokemon))
        if other:
            embed.add_field(
                name="Other Featured Pokemon",
                value=", ".join(other),
                inline=False
            )
        await channel.send(embed=embed)


@dataclass()
class Habitat:
    name: str
    pokemon: Dict[str, bool]
    times: List[int]


def setup(client):
    client.add_cog(GoFestCog(client))
