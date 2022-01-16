from pokeonta.cog import Cog
from discord import Guild, Member, utils


class Onboarding(Cog):
    @Cog.listener()
    async def on_ready(self):
        for member in self.client.guilds[0].members:
            if self.should_give_role(member):
                await self.assign_role(member)

    @Cog.listener()
    async def on_member_update(self, _, member: Member):
        if self.should_give_role(member):
            await self.assign_role(member)

    def should_give_role(self, member: Member):
        member_role = utils.get(member.guild.roles, name="member")
        if member_role in member.roles:
            return False

        instinct_role = utils.get(member.guild.roles, name="instinct")
        mystic_role = utils.get(member.guild.roles, name="mystic")
        valor_role = utils.get(member.guild.roles, name="valor")

        return len(set(member.roles) & {instinct_role, mystic_role, valor_role}) > 0

    async def assign_role(self, member: Member):
        member_role = utils.get(member.guild.roles, name="member")
        await member.add_roles(member_role)
        self.logger.debug(f"{member} has been given {member_role}")


def setup(client):
    client.add_cog(Onboarding(client))
