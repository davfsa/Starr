CREATE TABLE IF NOT EXISTS guilds (
    GuildID BIGINT NOT NULL PRIMARY KEY,
    Prefix TEXT DEFAULT '$',
    StarChannel BIGINT DEFAULT 0,
    Configured INT DEFAULT 0,
    Threshold INT DEFAULT 1
);

CREATE TABLE IF NOT EXISTS starboard_messages (
    StarMessageID BIGINT NOT NULL PRIMARY KEY,
    ReferenceID BIGINT NOT NULL
);
