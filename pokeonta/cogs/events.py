from __future__ import annotations
from discord.ext.commands import Context
from pokeonta.cog import Cog
from pokeonta.scheduler import schedule
from pokeonta.tags import tag
from pokeonta.models.events import Event
import asyncio
import datetime
import dateutil.parser
import dateutil.tz
import discord


class Events(Cog):
    def now(self) -> datetime.datetime:
        return datetime.datetime.now(dateutil.tz.gettz("America/New_York"))

    @Cog.group(aliases=("events",))
    async def event(self, ctx: Context):
        if not ctx.invoked_subcommand:
            now = self.now().replace(tzinfo=None)
            events = Event.filter(Event.ends > now)
            events = sorted(events, key=lambda event: event.starts)
            current = [event for event in events if event.starts <= now < event.ends]
            upcoming = [event for event in events if event.starts > now]

            def format_event(event: Event):
                title = f"[{event.title}]({event.link})" if event.link else event.title
                channel = self.client.get_channel(int(event.channel_id))
                return f"{title} ({event.starts:%b %-d}-{event.ends:%b %-d}) {channel.mention if channel else ''}"

            embed = discord.Embed(
                title="Current & Upcoming Events",
                description="" if events else "*No Events Found*"
            )
            if current:
                embed.add_field(
                    name="Current Events",
                    value="\n".join(format_event(event) for event in current),
                    inline=False
                )
            if upcoming:
                embed.add_field(
                    name="Upcoming Events",
                    value="\n".join(format_event(event) for event in upcoming),
                    inline = False
                )
            await ctx.send(embed=embed)

    @event.command()
    async def new(self, ctx: Context):
        fields = {
            "title": "What is the name of the event?",
            "description": "Give a brief description of the event",
            "link": "Is there an official link for this event?",
            "starts": "When does this event start? (`MM-DD-YYYY HH`, example \"June 1st 2020 @ 4pm\": `6-1-2020 16`)",
            "ends": "When does this event end? (`MM-DD-YYYY HH`, example \"June 1st 2020 @ 4pm\": `6-1-2020 16`)",
            "channel_id": "What channel should this event be in?"
        }
        values = {
            "title": None,
            "description": None,
            "link": None,
            "starts": None,
            "ends": None,
            "channel_id": None,
            "cancelled": False
        }

        def check(message: discord.Member) -> bool:
            if message.author.id != ctx.author.id:
                return False

            if message.channel.id != ctx.channel.id:
                return False

            return True

        for field, content in fields.items():
            await ctx.send(content)
            response = await self.client.wait_for("message", check=check)
            value = response.clean_content.strip()
            if field in {"starts", "ends"}:
                value = dateutil.parser.parse(value, ignoretz=True)
            elif field == "channel_id":
                value = response.raw_channel_mentions[0]
            values[field] = value

        preview = discord.Embed(
            description="Here is a preview of what you've entered. Hit the ✅ to create the event",
            title="Review Event Details"
        )
        preview.add_field(name="Title", value=values["title"], inline=False)
        preview.add_field(name="Description", value=values["description"], inline=False)
        preview.add_field(name="Link", value=f"[{values['link'][:32]}...]({values['link']})", inline=False)
        preview.add_field(name="Dates", value=f"{values['starts']:%B %-d %-I:%M%p} to {values['ends']:%B %-d %-I:%M%p}", inline=False)
        confirmation = await ctx.send(embed=preview)
        await confirmation.add_reaction("✅")

        def check(reaction: discord.Reaction, user: discord.User) -> bool:
            if ctx.author.id != user.id:
                return False

            if confirmation.id != reaction.message.id:
                return False

            return str(reaction.emoji) == "✅"

        try:
            reaction, _ = await self.client.wait_for("reaction_add", check=check, timeout=60)
        except asyncio.TimeoutError:
            await ctx.send("Canceled event creation.")
        else:
            event = Event(**values)
            event.save()
            self.schedule_event(values)
            await ctx.send(content=f"Event created")

    def schedule_event(self, event_dict):
        event = Event(**event_dict)
        when: datetime.datetime = event.starts.replace(tzinfo=self.now().tzinfo)
        handler = self.send_event_started
        if self.now() > when:
            when = event.ends.replace(tzinfo=self.now().tzinfo)
            handler = self.send_event_end
        elif when - self.now() > datetime.timedelta(days=1, hours=8):
            when = when - datetime.timedelta(days=1)
            handler = self.send_event_reminder
        event_dict["ends"] = event_dict["ends"].isoformat()
        event_dict["starts"] = event_dict["starts"].isoformat()
        print(when, self.now(), when - self.now())
        schedule("event", when - self.now(), handler, event_dict)

    async def send_event_message(self, event_dict, title: str):
        print(event_dict["starts"])
        event_dict["starts"] = datetime.datetime.fromisoformat(event_dict["starts"])
        event_dict["ends"] = datetime.datetime.fromisoformat(event_dict["ends"])
        event = Event(**event_dict)
        channel = self.client.get_channel(event.channel_id)
        await channel.send(
            embed=(
                discord.Embed(
                    description=event.description if event.ends > self.now() else "*This event is over*",
                    title=f"{title}: {event.title}"
                )
                .add_field(
                    name="Times",
                    value=(
                        f"Start: {event.starts:%B %-d, %-I:%M%p}\n"
                        f"End: {event.ends:%B %-d, %-I:%M%p}"
                    ),
                    inline=False
                )
                .add_field(
                    name="Details",
                    value=event.link,
                    inline=False
                )
            )
        )

    @tag("schedule", "event-reminder")
    async def send_event_reminder(self, event_dict):
        await self.send_event_message(event_dict, "Tomorrow")
        self.schedule_event(event_dict)

    @tag("schedule", "event-started")
    async def send_event_started(self, event_dict):
        await self.send_event_message(event_dict, "Now")
        self.schedule_event(event_dict)

    @tag("schedule", "event-ended")
    async def send_event_end(self, event_dict):
        await self.send_event_message(event_dict, "Ended")


def setup(client):
    client.add_cog(Events(client))
