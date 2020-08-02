from __future__ import annotations
from datetime import datetime, timedelta
from dateutil.tz import gettz
from discord.ext.commands import Context
from pokeonta.cog import Cog
from pokeonta.models.air_support_group import AirSupportGroup
from pokeonta.models.trainer_cards import TrainerCards
from pokeonta.scheduler import schedule
from pokeonta.tags import tag
from typing import Optional
import discord
import re


class AirSupportCog(Cog):
    @property
    def now(self) -> datetime:
        """ The current time in NY. """
        return datetime.now(gettz("America/New_York"))

    @Cog.command(aliases=("host", "h"))
    async def hosting(
        self, ctx: Context, raw_time: str, raid_type: str, *, location: str
    ):
        # Ensure that the user has filled out their trainer card so we can share their friend code
        if not self.is_trainer_card_complete(ctx.author):
            await ctx.send(
                f"{ctx.author.mention} you must fill out your trainer card with your trainer name and friend code.\n"
                f"```\n!trainer edit your_trainer_name your_friend_code\n```\n"
                f"Like this\n```\n!trainer edit ZZmmrmn 1234 5678 9012\n```"
            )
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

        message = await self.create_group_invite_message(
            ctx.author, time, raid_type, location
        )
        group = self.create_group(ctx.author, time, raid_type, location, message)
        self.schedule_expiration(group, message.channel)

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
        self,
        host: discord.Member,
        time: datetime,
        raid_type: str,
        location: str,
    ) -> discord.Message:
        channel = discord.utils.get(host.guild.channels, name="air-support")
        card = self.get_trainer_card(host.id)
        remote_emoji: discord.Emoji = discord.utils.get(channel.guild.emojis, name="remote")
        message = await channel.send(
            card.friend_code,
            embed=(
                discord.Embed(
                    description=(
                        f"Location: {location}\n"
                        f"Time: {time:%-I:%M%p}\n"
                        f"Raid: {raid_type}\n"
                    ),
                    title=f"@{host.display_name} is hosting a raid group!"
                )
                .add_field(
                    name="How To Join",
                    value=(
                        f"- React with {remote_emoji} to request an invite.\n"
                        f"- Add {host.mention} as a friend using their friend code above."
                    )
                )
                .set_thumbnail(url=remote_emoji.url)
            ),
        )
        await message.add_reaction(remote_emoji)
        return message

    @tag("schedule", "delete-air-support-group")
    async def delete_group(self, group_id: int, channel_id: int):
        group: AirSupportGroup = AirSupportGroup.get_by_id(group_id)
        channel: discord.TextChannel = self.client.get_channel(channel_id)
        if group:
            message = await channel.fetch_message(group.message_id)
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

    def parse_time(self, time_string: str) -> Optional[datetime]:
        match = re.match(r"^(?:(\d{1,2}?)[^\d]*(\d{2})|(\d+))$", time_string.strip())
        if not match:
            return

        hour, minute, duration = map(
            lambda value: int(value) if value else 0,
            match.groups()
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
        schedule("air-support-group-invite", when, self.delete_group, group.get_id(), channel.id)


def setup(client):
    client.add_cog(AirSupportCog(client))
