import hikari

from starr.bot import StarrBot


if __name__ == "__main__":
    dotenv.load_dotenv()  # FIXME: Would a config file be better? That way we can give an example of how it should be setup
    # config.yml.example
    
    StarrBot().run(
        activity=hikari.Activity(
            name="the stars!",
            type=hikari.ActivityType.WATCHING,
        )
    )
