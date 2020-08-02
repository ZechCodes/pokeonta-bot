import pokeonta.bootstrap
import pokeonta.scheduler


logger = pokeonta.bootstrap.setup_logger()
client = pokeonta.bootstrap.create_bot(logger)
pokeonta.bootstrap.load_cogs(client, logger)
pokeonta.bootstrap.connect_db(logger)
pokeonta.scheduler.initialize_scheduler(client.loop)
pokeonta.bootstrap.run(client, logger)
