import os
import psycopg2

_raw_url = os.environ.get("DATABASE_URL", "")
# Railway (and Heroku) emit postgres:// but psycopg2 requires postgresql://
DATABASE_URL = _raw_url.replace("postgres://", "postgresql://", 1)


def get_conn():
    conn = psycopg2.connect(DATABASE_URL)
    return conn


def dict_row(cur, row):
    if row is None:
        return None
    cols = [d[0] for d in cur.description]
    return dict(zip(cols, row))


def dict_rows(cur, rows):
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in rows]


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS pets (
            id              SERIAL PRIMARY KEY,
            name            TEXT NOT NULL UNIQUE,
            rarity          TEXT NOT NULL,
            value           TEXT NOT NULL DEFAULT '0',
            shiny_value         TEXT,
            prismatic_value     TEXT,
            rainbow_value       TEXT,
            image_url           TEXT,
            shiny_image_url     TEXT,
            prismatic_image_url TEXT,
            rainbow_image_url   TEXT,
            note                TEXT,
            exists_normal       TEXT DEFAULT '0',
            exists_shiny        TEXT DEFAULT '0',
            exists_prismatic    TEXT DEFAULT '0',
            exists_rainbow      TEXT DEFAULT '0',
            demand          INTEGER DEFAULT 0,
            trend           TEXT DEFAULT 'stable',
            description     TEXT,
            created_at      TEXT NOT NULL DEFAULT to_char(NOW(), 'YYYY-MM-DD HH24:MI:SS'),
            updated_at      TEXT NOT NULL DEFAULT to_char(NOW(), 'YYYY-MM-DD HH24:MI:SS')
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS value_history (
            id          SERIAL PRIMARY KEY,
            pet_id      INTEGER NOT NULL REFERENCES pets(id) ON DELETE CASCADE,
            pet_name    TEXT NOT NULL,
            old_value   TEXT NOT NULL,
            new_value   TEXT NOT NULL,
            old_shiny   TEXT,
            new_shiny   TEXT,
            changed_by  TEXT NOT NULL DEFAULT 'admin',
            reason      TEXT,
            changed_at  TEXT NOT NULL DEFAULT to_char(NOW(), 'YYYY-MM-DD HH24:MI:SS')
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS admin_users (
            id            SERIAL PRIMARY KEY,
            username      TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at    TEXT NOT NULL DEFAULT to_char(NOW(), 'YYYY-MM-DD HH24:MI:SS')
        )
    """)

    # Safe migrations — ADD COLUMN IF NOT EXISTS never errors on re-deploy
    safe_columns = [
        "ALTER TABLE pets ADD COLUMN IF NOT EXISTS image_url TEXT",
        "ALTER TABLE pets ADD COLUMN IF NOT EXISTS shiny_image_url TEXT",
        "ALTER TABLE pets ADD COLUMN IF NOT EXISTS prismatic_value TEXT",
        "ALTER TABLE pets ADD COLUMN IF NOT EXISTS rainbow_value TEXT",
        "ALTER TABLE pets ADD COLUMN IF NOT EXISTS prismatic_image_url TEXT",
        "ALTER TABLE pets ADD COLUMN IF NOT EXISTS rainbow_image_url TEXT",
        "ALTER TABLE pets ADD COLUMN IF NOT EXISTS exists_normal TEXT DEFAULT '0'",
        "ALTER TABLE pets ADD COLUMN IF NOT EXISTS exists_shiny TEXT DEFAULT '0'",
        "ALTER TABLE pets ADD COLUMN IF NOT EXISTS exists_prismatic TEXT DEFAULT '0'",
        "ALTER TABLE pets ADD COLUMN IF NOT EXISTS exists_rainbow TEXT DEFAULT '0'",
        "ALTER TABLE pets ADD COLUMN IF NOT EXISTS demand INTEGER DEFAULT 0",
        "ALTER TABLE pets ADD COLUMN IF NOT EXISTS trend TEXT DEFAULT 'stable'",
        "ALTER TABLE pets ADD COLUMN IF NOT EXISTS description TEXT",
    ]
    for sql in safe_columns:
        try:
            cur.execute(sql)
            conn.commit()
        except Exception:
            conn.rollback()

    conn.commit()
    cur.close()
    conn.close()
