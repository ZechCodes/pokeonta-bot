# Pokeonta Discord Bot
This is the discord bot for the Pokeonta discord server.

## Requirements
The bot uses [Poetry](https://python-poetry.org/) for packaging and dependency management. You will need to follow the [installation instructions](https://python-poetry.org/docs/#installation) before you can get started with the bot.

Additionally you will need a bot token from Discord. You can read about how to get yours [here](https://realpython.com/how-to-make-a-discord-bot-python/#creating-an-application).

## Configuration & Setup
First things first, we need to install all of the dependencies. To do that run:
```sh
poetry install
```
Next you need to configure the bot with the local dev settings. To do this copy the `development.example.yaml` file and name the new copy `development.yaml`. 

Once that’s done open it up and in the `bot` section change the `token` string to your dev bot token.
## Running
To run the bot you’ll need to be in the directory which you cloned the repo, and run the following command:
```sh
poetry run python -m pokeonta
```
This will create a virtual environment with all the required dependencies and run the pokeonta bot package.

Of course this will not have any real cogs enabled. By default the `development.yaml` only has the `devcog` enabled which allows you to load, unload, and reload cogs using discord commands. To enable a cog open `development.yaml` and in the `cogs` section find the cog you want and change its value from `false` to `true`. If it has an `enabled` field you’d update that field’s value to `true` instead. This allows you to work with just the cogs you are making changes to and not have to have them all running all the time.

## Database
We use PostgreSQL for the bot. If you’d like to run one locally we’ve included a Docker Compose file that will spin up a local server: `compose/postgres.yaml`. It’ll have the following config settings:
```
User: postgresadmin
Pass: dev-env-password-safe-to-be-public
DB:   pokeonta
Port: 5432
Host: 0.0.0.0
```
You’ll need to update `development.yaml` with your database configuration by changing the values in the `database` section.
