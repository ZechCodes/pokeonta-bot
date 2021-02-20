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
        self.exclusives = {
            "red": (
                "Ekans",
                "Oddish",
                "Mankey",
                "Growlithe",
                "Scyther",
                "Electabuzz",
            ),
            "green": (
                "Sandshrew",
                "Vulpix",
                "Meowth",
                "Bellsprout",
                "Magmar",
                "Pinsir",
            ),
        }
        self.hourly_features = [
            Habitat(
                name="Pallet Town",
                pokemon=[
                    "Bulbasaur",
                    "Charmander",
                    "Squirtle",
                    "Caterpie",
                    "Weedle",
                    "Pidgey",
                    "Rattata",
                    "Spearow",
                    "Pikachu",
                    "Zubat",
                ],
                times=[9, 14],
            ),
            Habitat(
                name="Pewter City",
                pokemon=[
                    "Nidoran ♀",
                    "Nidoran ♂",
                    "Clefairy",
                    "Paras",
                    "Diglett",
                    "Geodude",
                    "Magnemite",
                    "Onix",
                    "Voltorb",
                    "Rhyhorn",
                ],
                times=[10, 15],
            ),
            Habitat(
                name="Cerulean City",
                pokemon=[
                    "Jigglypuff",
                    "Psyduck",
                    "Poliwag",
                    "Tentacool",
                    "Shellder",
                    "Krabby",
                    "Horsea",
                    "Goldeen",
                    "Staryu",
                    "Magikarp",
                ],
                times=[11, 16],
            ),
            Habitat(
                name="Fuschia City",
                pokemon=[
                    "Venonat",
                    "Abra",
                    "Ponyta",
                    "Grimer",
                    "Gastly",
                    "Drowzee",
                    "Exeggcute",
                    "Koffing",
                    "Omanyte",
                    "Kabuto",
                ],
                times=[12, 17],
            ),
            Habitat(
                name="Pokemon League",
                pokemon=[
                    "Machop",
                    "Slowpoke",
                    "Doduo",
                    "Seel",
                    "Hitmonlee",
                    "Hitmonchan",
                    "Jynx",
                    "Eevee",
                    "Porygon",
                    "Dratini",
                ],
                times=[13, 18],
            ),
            Habitat(
                name="All Areas",
                pokemon=["*ALL POKEMON*"],
                times=[19],
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
            self.logger.debug("Scheduling location change")
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
            role = red if version.lower() == "red" else green
            nick = ctx.author.display_name
            if role in ctx.author.roles:
                nick = nick.replace(emoji, "")
                await ctx.author.remove_roles(role)
                message = f"{ctx.author.mention} you've been removed from {version.capitalize()}"
            elif version.lower() == "red":
                await ctx.author.remove_roles(green)
                await ctx.author.add_roles(red)
                nick = "🔴" + nick.replace("🟢", "")
            elif version.lower() == "green":
                await ctx.author.remove_roles(red)
                await ctx.author.add_roles(green)
                nick = "🟢" + nick.replace("🔴", "")

            await ctx.author.edit(nick=nick)

        await ctx.send(message)

    async def schedule_habitat_change(self):
        now = datetime.datetime.utcnow() - datetime.timedelta(hours=5)
        next_change = now.replace(hour=now.hour + 1, minute=0, second=0, microsecond=0)
        if now > datetime.datetime(2021, 2, 20, 7, 0, 0, 0):
            self.logger.debug(
                f"Next location change in {(next_change - now).seconds} for hour {now.hour + 1}"
            )
            await asyncio.sleep((next_change - now).seconds)

            await self.send_habitat_change(now.hour + 1)

            if now + datetime.timedelta(hours=2) < datetime.datetime(
                2021, 2, 20, 20, 0, 0, 0
            ):
                await asyncio.sleep(60)
                asyncio.get_event_loop().create_task(self.schedule_habitat_change())
        else:
            self.logger.debug(f"Too early to show a location")
            await asyncio.sleep((next_change - now).seconds)
            asyncio.get_event_loop().create_task(self.schedule_habitat_change())

    async def send_habitat_change(self, hour: int, current: bool = False):
        self.logger.debug(f"Looking for location in hour {hour}")
        for habitat in self.hourly_features:
            if hour in habitat.times:
                await self.send_habitat_message(habitat, current)
                break

    async def send_habitat_message(self, habitat: Habitat, current: bool = False):
        guild = self.client.get_guild(340162408498593793)
        channel: discord.TextChannel = discord.utils.get(
            guild.channels, name="kanto-celebration"
        )
        red = sorted(
            pokemon for pokemon in habitat.pokemon if pokemon in self.exclusives["red"]
        )
        green = sorted(
            pokemon
            for pokemon in habitat.pokemon
            if pokemon in self.exclusives["green"]
        )
        remaining = sorted(
            pokemon
            for pokemon in habitat.pokemon
            if pokemon not in self.exclusives["green"]
            and pokemon not in self.exclusives["red"]
        )
        embed = discord.Embed(
            title=f"We're currently in {habitat.name}"
            if current
            else f"We're now in {habitat.name}!!!"
        )
        if red:
            embed.add_field(
                name="🔴 Red Exclusives 🔴!!!",
                value=", ".join(red),
                inline=False,
            )
        if green:
            embed.add_field(
                name="🟢 Green Exclusives 🟢!!!",
                value=", ".join(green),
                inline=False,
            )
        if remaining:
            embed.add_field(
                name="⚪️ Featured Pokemon ⚪️!!!",
                value=", ".join(remaining),
                inline=False,
            )
        await channel.send(embed=embed)


@dataclass()
class Habitat:
    name: str
    pokemon: List[str]
    times: List[int]


def setup(client):
    client.add_cog(KantoCelebrationCog(client))
