from pokeonta.cog import Cog, commands


class GoFestCog(Cog):
    @Cog.listener()
    async def on_ready(self):
        self.logger.debug("Go Fest 2020 Cog is ready")


def setup(client):
    client.add_cog(GoFestCog(client))
