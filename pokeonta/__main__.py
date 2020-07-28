import pokeonta.bootstrap


logger = pokeonta.bootstrap.setup_logger()
pokeonta.bootstrap.connect_db(logger)
client = pokeonta.bootstrap.create_bot(logger)
pokeonta.bootstrap.load_cogs(client, logger)
pokeonta.bootstrap.run(client, logger)
