from __future__ import annotations

import typing as t
from os import environ
from collections import abc as collections
from pathlib import Path

import dotenv
import hikari
import tanjun

from starr import logging as starr_logging
from starr import models
from starr import database


class StarrBot(hikari.GatewayBot):

    __slots__ = ("_star", "_db_conn", "_guilds", "_logger", "_client")

    def __init__(self, *args: collections.Sequence[t.Any], **kargs: collections.Mapping[str, t.Any]) -> None:
        super().__init__(
            intents=(
                hikari.Intents.GUILD_MESSAGE_REACTIONS |
                hikari.Intents.GUILD_MESSAGES |
                hikari.Intents.GUILDS
            ),
            *args,
            **kwargs,
        )
        self._client = (
            tanjun.Client.from_gateway_bot(
                self,
                mention_prefix=True,
                declare_global_commands=int(environ.get("DEV_GUILD_ID", 0)) or True,
            )
            .set_prefix_getter(self.resolve_prefix)
            .load_modules(*Path("./starr/modules").glob("*.py"))
        )

        self._star = "⭐"  # FIXME: Change to be cross compatible on Discord and stored as. Maybe even move it out of here? 
        self._logger = starr_logging.setup_file_logger()
        self._db_conn = database.Database()
        self._guilds = {}

        subscriptions: dict[
            t.Type[hikari.Event], t.Callable[[t.Any], t.Coroutine[t.Any, t.Any, None]]  # FIXME; Could this be cleaned up?
        ] = {
            hikari.StartingEvent: self.on_starting,
            hikari.StartedEvent: self.on_started,
            hikari.StoppedEvent: self.on_stopping,
            hikari.GuildAvailableEvent: self.on_guild_available,
            hikari.GuildJoinEvent: self.on_guild_available,
        }

        for event, callback in subscriptions.items():
            self.subscribe(event, callback)

    async def on_starting(self, _: hikari.StartingEvent) -> None:
        await self.db.connect()

    async def on_started(self, _: hikari.StartedEvent) -> None:
        if data := await self.db.rows("SELECT * FROM guilds;"):
            for guild in data:
                self.guilds.insert(StarrGuild(*guild))

    async def on_stopping(self, _: hikari.StoppedEvent) -> None:
        await self.db.close()

    async def on_guild_available(
        self,
        event: hikari.GuildAvailableEvent | hikari.GuildJoinEvent
    ) -> None:
        if event.guild_id not in self._guilds:
            guild = await StarrGuild.default_with_insert(self.db, event.guild_id)
            self._guilds.insert(guild)

    async def resolve_prefix(self, ctx: tanjun.MessageContext) -> tuple[str]:
        assert ctx.guild_id is not None

        if guild := self._guilds.get(ctx.guild_id):
            return guild.prefix,

        return ("$",)
