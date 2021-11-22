from __future__ import annotations

import asyncio
import functools
import typing as t
from os import environ

import asyncpg


class Database:
    """Wrapper class for AsyncPG Database access."""

    __slots__ = ("_pool",)

    def __init__(self) -> None:
        # self.db = environ["PG_DB"]
        # self.host = environ["PG_HOST"]
        # self.user = environ["PG_USER"]
        # self.password = environ["PG_PASS"]
        # self.port = environ["PG_PORT"]
        # self.schema = "./starr/data/schema.sql"
        self._pool: asyncpg.Pool = NotImplemented

    async def connect(self, database: str, user: str, password: str, host: str, port: str, schema_path: str) -> None:
        """Opens a connection pool."""
        self._pool = await asyncpg.create_pool(
            database=databse,
            user=user,
            password=password,
            host=host,
            port=port,
        )

        await self.execute_script(self.schema)

    async def close(self) -> None:
        """Closes the connection pool."""
        await self._pool.close()

    def with_connection(func: t.Callable[..., t.Any]) -> t.Callable[..., t.Any]:  # type: ignore
        """A decorator used to acquire a connection from the pool."""

        @functools.wraps(func)
        async def wrapper(self: "Database", *args: t.Any) -> t.Any:
            async with self._pool.acquire() as conn:
                return await func(self, *args, conn=conn)

        return wrapper

    # FIXME: RENAMED ALL BELLOW, MAKE SURE OTHERS ARE RENAMED TOO

    @with_connection
    async def fetch_value(self, q: str, *values: t.Any, conn: asyncpg.Connection) -> t.Optional[t.Any]:
        """Read 1 field of applicable data."""
        query = await conn.prepare(q)
        return await query.fetchval(*values)

    @with_connection
    async def fetch_row(
        self, q: str, *values: t.Any, conn: asyncpg.Connection
    ) -> t.Optional[t.List[t.Any]]:
        """Read 1 row of applicable data."""
        query = await conn.prepare(q)
        if data := await query.fetchrow(*values):
            return [r for r in data]

        return None

    @with_connection
    async def fetch_rows(
        self, q: str, *values: t.Any, conn: asyncpg.Connection
    ) -> t.Optional[t.List[t.Iterable[t.Any]]]:
        """Read all rows of applicable data."""
        query = await conn.prepare(q)
        if data := await query.fetch(*values):
            return [*map(lambda r: tuple(r.values()), data)]

        return None

    @with_connection
    async def fetch_column(self, q: str, *values: t.Any, conn: asyncpg.Connection) -> t.List[t.Any]:
        """Read a single column of applicable data."""
        query = await conn.prepare(q)
        return [r[0] for r in await query.fetch(*values)]

    @with_connection
    async def execute(self, q: str, *values: t.Any, conn: asyncpg.Connection) -> None:
        """Execute a write operation on the database."""
        query = await conn.prepare(q)
        await query.fetch(*values)  # FIXME: Is this correct?

    @with_connection
    async def execute_many(
        self, q: str, values: t.List[t.Iterable[t.Any]], conn: asyncpg.Connection
    ) -> None:
        """Execute a write operation for each set of values."""
        query = await conn.prepare(q)
        await query.executemany(values)

    @with_connection
    async def execute_script(self, path: str, conn: asyncpg.Connection) -> None:  # FIXME: This might not want to be exposed, since it is blocking
        """Execute an sql script at a given path."""
        with open(path) as script:
            await conn.execute(script.read())
