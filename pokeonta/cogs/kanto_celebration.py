from __future__ import annotations
from pokeonta.cog import Cog
from dataclasses import dataclass
from discord.ext.commands import Context
from typing import Dict, List
import asyncio
import datetime
import discord


class KantoCelebrationCog(Cog):
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
                times=[],
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
                    "**Woobat**": True,
                },
                times=[13],
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
                    "**Heatmor**": True,
                },
                times=[11],
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
                    "Alomomola": False,
                },
                times=[12],
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
                    "Ferroseed": False,
                },
                times=[],
            ),
        ]

    @Cog.command()
    async def habitat(self, ctx):
        now = datetime.datetime.utcnow() - datetime.timedelta(hours=5)
        await self.send_habitat_change(now.hour, current=True)

    async def ready(self):
        if datetime.datetime.utcnow() - datetime.timedelta(hours=5) < datetime.datetime(
            2021, 2, 20, 20, 0, 0, 0
        ):
            self.logger.debug("Scheduling habitat change")
            asyncio.get_event_loop().create_task(self.schedule_habitat_change())

    @Cog.command(aliases=["v"])
    async def version(self, ctx: Context, version: str):
        emoji = {"red": "🔴", "green": "🟢"}.get(version.lower())
        message = f"{ctx.author.mention} you've been added to **{emoji}{version.capitalize()}{emoji}** version"

        if not emoji:
            message = (
                f"{ctx.author.mention} you need to select either 'Red' or 'Green' 😉"
            )
        else:
            red, green = (
                discord.utils.get(ctx.guild.roles, name="red"),
                discord.utils.get(ctx.guild.roles, name="green"),
            )
            role = red if version == "red" else green
            nick = ctx.author.display_name
            if role in ctx.author.roles:
                nick = nick.replace(emoji, "")
                await ctx.author.remove_roles(role)
                message = f"{ctx.author.mention} you've been removed from {version.capitalize()}"
            elif version == "red":
                await ctx.author.remove_roles(green)
                await ctx.author.add_roles(red)
                nick = "🔴" + nick.replace("🟢", "")
            elif version == "green":
                await ctx.author.remove_roles(red)
                await ctx.author.add_roles(green)
                nick = "🟢" + nick.replace("🔴", "")

            await ctx.author.edit(nick=nick)

        await ctx.send(message)

    async def schedule_habitat_change(self):
        return
        now = datetime.datetime.utcnow() - datetime.timedelta(hours=5)
        next_change = now.replace(hour=now.hour + 1, minute=0, second=0, microsecond=0)
        self.logger.debug(
            f"Next habitat change in {(next_change - now).seconds} for hour {now.hour + 1}"
        )
        await asyncio.sleep((next_change - now).seconds)

        await self.send_habitat_change(now.hour + 1)
        if now + datetime.timedelta(hours=2) < datetime.datetime(
            2020, 8, 16, 20, 0, 0, 0
        ):
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
        channel: discord.TextChannel = discord.utils.get(
            guild.channels, name="go-fest-aug-16"
        )
        embed = discord.Embed(
            title=f"We're currently in the {habitat.name} habitat"
            if current
            else f"We're now in the {habitat.name} Habitat!!!"
        ).add_field(
            name="Featured Shinies!!!",
            value=", ".join(
                filter(lambda pokemon: habitat.pokemon[pokemon], habitat.pokemon)
            ),
            inline=False,
        )
        other = list(
            filter(lambda pokemon: not habitat.pokemon[pokemon], habitat.pokemon)
        )
        if other:
            embed.add_field(
                name="Other Featured Pokemon", value=", ".join(other), inline=False
            )
        await channel.send(embed=embed)


@dataclass()
class Habitat:
    name: str
    pokemon: Dict[str, bool]
    times: List[int]


def setup(client):
    client.add_cog(KantoCelebrationCog(client))
