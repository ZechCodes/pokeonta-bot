from __future__ import annotations
from dataclasses import dataclass
from discord.ext.commands import Context
from pokeonta.cog import Cog
from typing import List
import csv
import discord
import pathlib


class GymsCog(Cog):
    def __init__(self, client):
        super().__init__(client)
        self.gyms = self.load_gyms()
        self.logger.debug(f"Found {len(self.gyms)} gyms")
        import pprint
        pprint.pprint(self.gyms)

    def load_gyms(self) -> List[Gym]:
        path = pathlib.Path(__file__).parent.parent / "gyms.csv"
        with path.open() as gyms_file:
            return [
                Gym(
                    name=row[0],
                    nick=row[1],
                    lat=float(row[2]),
                    lng=float(row[3]),
                    ex=row[4] == "TRUE"
                )
                for row in list(csv.reader(gyms_file))[1:]
            ]

    @Cog.command(aliases=("where", "directions", "map", "g"))
    async def gym(self, ctx: Context, search: str):
        gyms = self.find_matching_gyms(search)

        title = f"No gyms found that match {search!r}"
        if len(gyms) > 1:
            title = f"Found {len(gyms)} gyms for {search!r}"
        elif len(gyms) == 1:
            title = f"Found 1 gym for {search!r}"

        await self.send_gym_list(ctx.channel, title, gyms)

    @Cog.command(aliases=("ex", "exgym"))
    async def exgyms(self, ctx: Context):
        gyms = self.find_ex_gyms()
        title = f"No EX gyms found"
        if len(gyms) > 1:
            title = f"Found {len(gyms)} EX Gyms"
        elif len(gyms) == 1:
            title = f"Found 1 EX Gym"

        await self.send_gym_list(ctx.channel, title, gyms)

    async def send_gym_list(self, channel: discord.TextChannel, title: str, gyms: List[Gym]):
        ex_emoji: discord.Emoji = discord.utils.get(channel.guild.emojis, name="exraid")
        pass_emoji: discord.Emoji = discord.utils.get(channel.guild.emojis, name="raidpass")

        await channel.send(
            embed=discord.Embed(
                description="\n".join(
                    f"{ex_emoji if gym.ex else pass_emoji} [{gym.name}](http://www.google.com/maps/place/{gym.lat},{gym.lng})"
                    for gym in gyms
                ),
                title=title
            ).set_footer(
                text="Click any of the gyms for directions",
                icon_url=(
                    "https://raw.githubusercontent.com/ZeChrales/PogoAssets/master/static_assets/png/ActivityLogGymLogo.png"
                )
            )
        )

    def find_ex_gyms(self) -> List[Gym]:
        return sorted(
            (gym for gym in self.gyms if gym.ex),
            key=lambda gym: gym.name
        )

    def find_matching_gyms(self, search: str) -> List[Gym]:
        return sorted(
            (gym for gym in self.gyms if search.casefold() in (gym.name + gym.nick).casefold()),
            key=lambda gym: gym.name
        )


@dataclass
class Gym:
    name: str
    nick: str
    lat: float
    lng: float
    ex: bool


def setup(client):
    client.add_cog(GymsCog(client))