from __future__ import annotations

import typing
from dataclasses import dataclass, field

import hikari

from starr import database


@dataclass(slots=True)
class StarrGuild:
    guild_id: int  # .id or .discord_id ?
    prefix: str
    star_channel: int = 0
    configured: int = 0
    threshold: int = 1

    @classmethod
    async def from_db(cls, db: database.Database, guild_id: int) -> StarrGuild:
        data = await db.row("SELECT * FROM guilds WHERE GuildID = $1;", guild_id)
        return cls(*data)

    @classmethod
    async def default_with_insert(cls, db: database.Database, guild_id: int) -> StarrGuild:
        data = await db.row(
            "INSERT INTO guilds (GuildID) VALUES ($1) "
            "ON CONFLICT DO NOTHING RETURNING *;",
            guild_id
        )

        if not data:
            return await cls.from_db(db, guild_id)

        return cls(*data)


@dataclass(slots=True)
class StarboardMessage:
    message_id: int
    reference_id: int
    guild: StarrGuild

    async def db_insert(self, db: database.Database) -> None:
        await db.execute(
            "INSERT INTO starboard_messages (StarMessageID, ReferenceID) "
            "VALUES ($1, $2) ON CONFLICT DO NOTHING;",
            self.message_id,
            self.reference_id,
        )

    async def db_update(self, db: database.Database) -> None:
        # FIXME: Why 2 calls?
        # Additionally, each of these will fetch a connection, so shouldnt each one acquire a new DatabaseConn object and then you can call methods on it?
        await db.execute(
            "DELETE FROM starboard_messages WHERE ReferenceID = $1",
            self.reference_id
        )
        await db.execute(
            "UPDATE starboard_messages SET StarMessageID = $1 WHERE ReferenceID = $2;",
            self.message_id,
            self.reference_id,
        )

    async def delete(self, rest: hikari.api.RESTClient, db: database.Database) -> None:
        try:
            await rest.delete_message(self.guild.star_channel, self.message_id)
        except hikari.NotFoundError:
            # The starboard message was already deleted.
            pass

        await db.execute("DELETE FROM starboard_messages WHERE StarMessageID = $1;", self.message_id)

    async def update(
        self,
        rest: hikari.api.RESTClient,
        db: Database,
        message: hikari.Message,
        count: int,
        guild: StarrGuild,
    ) -> None:
        try:
            message = await rest.fetch_message(guild.star_channel, self.message_id)

        except hikari.NotFoundError:
            message = await self.create_new(rest, db, message, count, guild)  # FIXME: Why create a new class?
            self.message_id = message.id
            await self.db_update(db)

        else:
            await message.edit(f"You're a ⭐ x{count}!")  # FIXME: Remove unicode emoji

    @classmethod
    async def from_reference(
        cls,
        db: Database,
        reference_id: int,
        guild: StarrGuild,
    ) -> StarboardMessage | None:
        data = await db.fetch(  # One liner?
            "SELECT StarMessageID FROM starboard_messages "
            "WHERE ReferenceID = $1",
            reference_id,
        )

        if data:
            return cls(data, reference_id, guild)

        return None

    @classmethod
    async def create_new(
        cls,
        rest: hikari.api.RESTClient,
        db: Database,
        message: hikari.Message,
        count: int,
        guild: StarrGuild,
    ) -> hikari.Message:
        embed = (
            hikari.Embed(
                title=f"Jump to message",
                url=message.make_link(guild.guild_id),
                color=hikari.Color.from_hex_code("#fcd303"),  # FIXME: This could be moved to a constant instead of re-recreating all the time
                description=message.content,
                timestamp=message.timestamp,
            )
            .set_author(
                name=str(message.author),
                icon=message.author.avatar_url or message.author.default_avatar_url,
            )
            .set_footer(text=f"ID: {message.id}")
        )

        if message.attachments:
            embed.set_image(message.attachments[0])

        new_message = await rest.create_message(
            guild.star_channel,
            f"You're a ⭐ x{count}!",  # FIXME: Remove unicode emoji
            embed=embed,
        )

        starboard_message = cls(new_message.id, message.id, guild)
        await starboard_message.db_insert(db)
        return new_message
