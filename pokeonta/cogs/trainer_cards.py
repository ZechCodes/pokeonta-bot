from __future__ import annotations
from pokeonta.cog import Cog
from pokeonta.models.trainer_cards import TrainerCards as TrainerCardsModel
from typing import Optional
import discord
import discord.ext.commands as commands
import re


class TrainerCards(Cog):
    @Cog.group(aliases=("t",))
    async def trainer(self, ctx: commands.Context, member: Optional[discord.Member] = None):
        if ctx.invoked_subcommand is None:
            await self.show_trainer_card(member if member else ctx.author, ctx.channel)

    @trainer.command()
    async def edit(self, ctx: commands.Context, ign: str, *, friend_code: Optional[str] = ""):
        friend_code = re.sub(r"[^\d]", "", friend_code)
        card = self.get_trainer_card(ctx.author.id)
        if not card:
            card = TrainerCardsModel(user_id=ctx.author.id, trainer_name=ign, friend_code=friend_code)
        else:
            card.name = ign
            card.friend_code = friend_code
        card.save()

        await ctx.send(f"Here is your updated trainer card")
        await self.show_trainer_card(ctx.author, ctx.channel)

    @trainer.command(aliases=("h", "?"))
    async def help(self, ctx: commands.Context):
        await ctx.send(
            embed=discord.Embed(
                title="Trainer Card Help",
                description=(
                    "The trainer card is a quick and easy way to find the in game details for a discord user. If "
                    "they've opted to share their friend code you'll even be able to long press it on the trainer card "
                    "to copy it!"
                )
            )
            .add_field(
                name="Looking Up Users",
                value=(
                    "To look up a user's trainer card just type in the trainer command and tag the user.\nLike this:\n"
                    "```\n!trainer @Zech\n```"
                ),
                inline=False
            )
            .add_field(
                name="Sharing Your Card",
                value=(
                    "You can show your own card by typing in just the trainer command.\nLike this:\n"
                    "```\n!trainer\n```"
                ),
                inline=False
            )
            .add_field(
                name="Updating Your Trainer Card",
                value=(
                    "You can change what is on your trainer card by typing in the trainer edit command and follow it "
                    "with your trainer name and then your friend code. If you wouldn't like to share your friend code "
                    "you can just omit it.\nLike this:\n"
                    "```\n!trainer edit ZZmmrmn 0000 0000 0000\n```\nOr if you don't want to share your friend code:\n"
                    "```\n!trainer edit ZZmmrmn\n```"
                ),
                inline=False
            )
            .add_field(
                name="Tips",
                value=(
                    "You can shorten the command from `!trainer` to `!t` ;)!d"
                ),
                inline=False
            )
        )

    async def show_trainer_card(self, member: discord.Member, channel: discord.TextChannel):
        card = self.get_trainer_card(member.id)
        message = {}
        if not card:
            message["description"] = f"They have not yet setup their trainer card."
        else:
            message["About"] = f"Their in game name is *{card.trainer_name}*"
            message["description"] = self.format_code(card.friend_code) if card.friend_code else "*They have not set a friend code*"

        embed = (
            discord.Embed(
                title=f"{member.display_name}'s Trainer Card",
                description=message.pop("description")
            )
            .set_thumbnail(url=member.avatar_url)
            .set_footer(text="!trainer help | !trainer @username | !trainer edit")
        )
        for title, content in message.items():
            embed.add_field(name=title, value=content, inline=False)

        await channel.send(embed=embed)

    def format_code(self, code: str) -> str:
        sections = re.findall(r"\d{1,4}", code)
        return " ".join(sections)

    def get_trainer_card(self, member_id: int) -> Optional[TrainerCardsModel]:
        return TrainerCardsModel.get_or_none(TrainerCardsModel.user_id == member_id)


def setup(client):
    client.add_cog(TrainerCards(client))
