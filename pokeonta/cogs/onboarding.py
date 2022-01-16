from pokeonta.cog import Cog
from discord import Member, utils


class Onboarding(Cog):
    @Cog.listener()
    async def on_member_update(self, before: Member, member: Member):
        instinct_role = utils.get(member.guild.roles, name="instinct")
        member_role = utils.get(member.guild.roles, name="member")
        mystic_role = utils.get(member.guild.roles, name="mystic")
        valor_role = utils.get(member.guild.roles, name="valor")

        if member_role in before.roles:
            return

        if set(member.roles) & {instinct_role, mystic_role, valor_role}:
            return

        await member.add_roles(member_role)


def setup(client):
    client.add_cog(Onboarding(client))
