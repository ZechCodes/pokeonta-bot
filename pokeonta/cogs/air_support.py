from __future__ import annotations
from datetime import datetime, timedelta
from dateutil.tz import gettz
from discord.ext.commands import Context, has_guild_permissions
from functools import lru_cache
from pokeonta.cog import Cog
from pokeonta.models.air_support_group import AirSupportGroup
from pokeonta.models.trainer_cards import TrainerCards
from pokeonta.scheduler import schedule
from pokeonta.tags import tag
from typing import List, Optional
import discord
import re


class Colors:
    BLUE = 0x4444CC
    GREEN = 0x00AA44
    YELLOW = 0xCC9900


class Embed(discord.Embed):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_footer(text="!hosting time pokemon/level location")


class AirSupportCog(Cog):
    @lru_cache()
    def air_support_channel(self, guild: discord.Guild) -> discord.TextChannel:
        return discord.utils.get(guild.channels, name="air-support")

    @property
    def now(self) -> datetime:
        """ The current time in NY. """
        return datetime.now(gettz("America/New_York"))

    @Cog.command()
    @has_guild_permissions(manage_channels=True)
    async def setup(self, ctx: Context):
        channel = self.air_support_channel(ctx.guild)
        emoji = discord.utils.get(ctx.guild.emojis, name="remote")
        await ctx.message.delete()
        await channel.send(
            embed=discord.Embed(color=Colors.BLUE, title="Remote Raid Hosting")
            .add_field(
                name="Hosting A Raid",
                value=(
                    "You can broadcast that you can invite people to a raid using the `!hosting` command.```\n!hosting "
                    "15 Gible Vander\n!hosting 1:30 Rayquaza Fire Dog\n!hosting 12:00 5* Elm Park Gym\n```\n*Example "
                    "1:* a Gible raid at vander in 15 minutes\n*Example 2:* Rayquaza raid at Fire Dog at 1:30\n*Example"
                    " 3:* Elm Park for a legendary with a 12 o'clock pull."
                ),
                inline=False,
            )
            .add_field(
                name="Seeing Invites",
                value="You can see who has requested an invite using the `!invites` command:```\n!invites Vander\n```",
                inline=False,
            )
            .add_field(
                name="Trainer Card",
                value=(
                    "In order to use this feature you must have a trainer card with a friend code setup. To do that "
                    "this command:```\n!trainer edit trainer_name friend_code\n```"
                ),
                inline=False,
            )
            .set_thumbnail(
                url="https://raw.githubusercontent.com/ZeChrales/PogoAssets/master/static_assets/png/Item_1408_5.png"
            )
        )

    @Cog.group(aliases=("host", "h"))
    async def hosting(
        self,
        ctx: Context,
        raw_time: str,
        raid_type: str = None,
        *,
        location: str = None,
    ):
        if ctx.invoked_subcommand:
            return

        if raid_type is None or location is None:
            await ctx.send(
                "You must tell us what the pokemon/raid level is and the location.```\n!hosting 10 Gible Vander\n```"
            )
            return

        # Ensure that the user has filled out their trainer card so we can share their friend code
        if not self.is_trainer_card_complete(ctx.author):
            await self.send_trainer_card_instructions(ctx.channel, ctx.author)
            return

        # Ensure the time is a proper format and that it's not so far in the future that it can't exist
        time = self.parse_time(raw_time)
        if not time or time - self.now >= timedelta(hours=1, minutes=45):
            await ctx.send(
                f"{ctx.author.mention} `{raw_time}` is either not a valid time or is too far in the future."
            )
            return

        # Ensure the location is unique for this member
        if self.get_group(ctx.author, location):
            await ctx.send(
                f"{ctx.author.mention} you've already created a group for `{location}`, "
                f"if it has already ended cancel it:\n```\n!cancel {location}\n```"
            )
            return

        raid_type = self.map_raid_type(raid_type, ctx.guild)

        message = await self.create_group_invite_message(
            ctx.author, time, raid_type, location
        )
        group = self.create_group(ctx.author, time, raid_type, location, message)
        self.schedule_expiration(group, message.channel)

        await ctx.send(
            embed=Embed(
                color=Colors.GREEN,
                description=(
                    f"{ctx.author.mention} is hosting a {raid_type} raid! You can join them "
                    f"[here]({message.jump_url})."
                ),
            )
        )

    @Cog.command(aliases=("done", "d"))
    async def cancel(self, ctx: Context, *, location: str):
        group = self.get_group(ctx.author, location)
        if not group:
            await ctx.send("Group was already canceled or was never created")
            return

        rsvps = list(
            filter(lambda rsvp: not rsvp.bot, await self.get_rsvps(group, ctx.guild))
        )
        await self.delete_group(group.id, self.air_support_channel(ctx.guild).id)

        time = group.time.replace(tzinfo=gettz("UTC")).astimezone(gettz("America/New_York"))
        message = (
            f"{ctx.author.mention} You've canceled your raid group at {group.location} for a {group.raid_type} at "
            f"{time:%-I:%M%p}\nDropping RSVPs from: "
            f"{' '.join(rsvp.mention for rsvp in rsvps) if rsvps else '*No RSVPs Found*'}"
        )
        if ctx.command != "cancel":
            message = (
                f"{ctx.author.mention} Removing the group at {group.location} for a {group.raid_type} at "
                f"{time:%-I:%M%p}"
            )
        await ctx.send(message)

    @Cog.command(aliases=("invite", "i"))
    async def invites(self, ctx: Context, *, location: str):
        group = self.get_group(ctx.author, location)
        if not group:
            await ctx.send("Couldn't find a group for that location")
            return

        message = []
        rsvps = filter(
            lambda rsvp: not rsvp.bot, await self.get_rsvps(group, ctx.guild)
        )
        for rsvp in rsvps:
            card = self.get_trainer_card(rsvp.id)
            message.append(f"{rsvp.mention} - IGN: *{card.trainer_name}*")

        await ctx.send(
            ctx.author.mention,
            embed=Embed(
                description="\n".join(message) if message else "*No RSVPs Found*",
                title=f"RSVPs for {group.location}",
                color=Colors.GREEN,
            ),
        )

    @Cog.listener()
    async def on_raw_reaction_add(self, reaction: discord.RawReactionActionEvent):
        if reaction.member.bot:
            return

        guild: discord.Guild = self.client.get_guild(reaction.guild_id)
        if reaction.channel_id != self.air_support_channel(guild).id:
            return

        group = self.get_group_by_message_id(reaction.message_id)
        if not group:
            return

        if reaction.emoji.name not in {"raidpass", "remote"}:
            return

        host = guild.get_member(group.host_id)
        raids = discord.utils.get(guild.channels, name="raids")
        message = await self.get_message(
            self.air_support_channel(guild), reaction.message_id
        )
        if reaction.emoji.name == "remote":
            if not self.is_trainer_card_complete(reaction.member):
                await self.send_trainer_card_instructions(raids, reaction.member, 30)
                await message.remove_reaction(reaction.emoji, reaction.member)
                return

            card = self.get_trainer_card(reaction.member.id)
            await raids.send(
                card.friend_code,
                embed=Embed(
                    description=(
                        f"{reaction.member.mention} would like to join {host.mention} at "
                        f"[{group.location}]({message.jump_url}) {reaction.emoji}\nGet their friend code above."
                    )
                )
            )
        elif reaction.emoji.name == "raidpass":
            await raids.send(
                embed=Embed(
                    description=(
                        f"{reaction.member.mention} will be joining {host.mention} at "
                        f"[{group.location}]({message.jump_url}) {reaction.emoji}"
                    )
                )
            )

    async def get_message(
        self, channel: discord.TextChannel, message_id: int
    ) -> Optional[discord.Message]:
        try:
            return await channel.fetch_message(message_id)
        except discord.errors.NotFound:
            return

    # Helper Functions

    def create_group(
        self,
        host: discord.Member,
        time: datetime,
        raid_type: str,
        location: str,
        message: discord.Message,
    ) -> AirSupportGroup:
        group = AirSupportGroup(
            host_id=host.id,
            raid_type=raid_type,
            time=time,
            location=location.casefold(),
            message_id=message.id,
        )
        group.save()
        return group

    async def create_group_invite_message(
        self, host: discord.Member, time: datetime, raid_type: str, location: str,
    ) -> discord.Message:
        card = self.get_trainer_card(host.id)
        remote_emoji: discord.Emoji = discord.utils.get(
            host.guild.emojis, name="remote"
        )
        raid_pass_emoji: discord.Emoji = discord.utils.get(
            host.guild.emojis, name="raidpass"
        )
        message = await self.air_support_channel(host.guild).send(
            card.friend_code,
            embed=(
                Embed(
                    description=(
                        f"Location: {location}\n"
                        f"Time: {time:%-I:%M%p}\n"
                        f"Raid: {raid_type}\n"
                    ),
                    title=f"@{host.display_name} is hosting a raid group!",
                )
                .add_field(
                    name="How To Join",
                    value=(
                        f"- React with {remote_emoji} to request an invite.\n"
                        f"- React with {raid_pass_emoji} if you're doing it and don't need an invite.\n"
                        f"- Add {host.mention} as a friend using their friend code above."
                    ),
                )
                .set_thumbnail(url=remote_emoji.url)
            ),
        )
        await message.add_reaction(remote_emoji)
        await message.add_reaction(raid_pass_emoji)
        return message

    @tag("schedule", "delete-air-support-group")
    async def delete_group(self, group_id: int, channel_id: int):
        group: AirSupportGroup = AirSupportGroup.get_by_id(group_id)
        channel: discord.TextChannel = self.client.get_channel(channel_id)
        if group:
            message = await self.get_message(channel, group.message_id)
            if message:
                await message.delete()

            group.delete_instance()

    def get_group(
        self, member: discord.Member, location: str
    ) -> Optional[AirSupportGroup]:
        return AirSupportGroup.get_or_none(
            AirSupportGroup.host_id == member.id,
            AirSupportGroup.location == location.casefold(),
        )

    def get_group_by_message_id(self, message_id: int) -> Optional[AirSupportGroup]:
        return AirSupportGroup.get_or_none(AirSupportGroup.message_id == message_id)

    async def get_rsvps(
        self, group: AirSupportGroup, guild: discord.Guild
    ) -> List[discord.Member]:
        channel = self.air_support_channel(guild)
        message = await self.get_message(channel, group.message_id)
        if not message:
            return []

        emoji = discord.utils.get(message.guild.emojis, name="remote")
        return await discord.utils.get(message.reactions, emoji=emoji).users().flatten()

    def get_trainer_card(self, member_id: int) -> Optional[TrainerCards]:
        """ Gets a trainer card for a member. """
        return TrainerCards.get_or_none(TrainerCards.user_id == member_id)

    def is_trainer_card_complete(self, member: discord.Member) -> bool:
        """ Checks that a member has setup a trainer and that it has a trainer name and friend code. """
        card = self.get_trainer_card(member.id)
        if not card:
            return False

        if not card.friend_code:
            return False

        if not card.trainer_name:
            return False

        return True

    def map_raid_type(self, raid_type: str, guild: discord.Guild) -> str:
        raid_map = {
            "5*": "legendary",
            "legendary": "legendary",
            "leg": "legendary",
            "rayquaza": "rayquaza",
            "ray": "rayquaza",
            "rayray": "rayquaza",
        }
        emoji = discord.utils.get(
            guild.emojis, name=raid_map.get(raid_type.casefold(), raid_type.casefold())
        )
        if not emoji:
            return raid_type

        return emoji

    def parse_time(self, time_string: str) -> Optional[datetime]:
        match = re.match(r"^(?:(\d{1,2}?)[^\d]*(\d{2})|(\d+))$", time_string.strip())
        if not match:
            return

        hour, minute, duration = map(
            lambda value: int(value) if value else 0, match.groups()
        )

        # Is it a time?
        if hour:
            time = self.now.replace(hour=hour, minute=minute)
            if time < self.now:
                time = time + timedelta(hours=12)

            return time

        # It must be a duration in minutes
        return self.now + timedelta(minutes=duration)

    def schedule_expiration(self, group: AirSupportGroup, channel: discord.TextChannel):
        when = (group.time + timedelta(minutes=45)) - self.now
        schedule(
            "air-support-group-invite",
            when,
            self.delete_group,
            group.get_id(),
            channel.id,
        )

    async def send_trainer_card_instructions(
        self,
        channel: discord.TextChannel,
        member: discord.Member,
        delete_after: Optional[int] = None,
    ):
        await channel.send(
            member.mention,
            embed=Embed(
                description=(
                    f"You must fill out your trainer card with your trainer name and friend code.\n"
                    f"```\n!trainer edit your_trainer_name your_friend_code\n```\n"
                    f"Like this\n```\n!trainer edit ZZmmrmn 1234 5678 9012\n```"
                ),
                color=Colors.YELLOW,
            ),
            delete_after=delete_after,
        )


def setup(client):
    client.add_cog(AirSupportCog(client))
