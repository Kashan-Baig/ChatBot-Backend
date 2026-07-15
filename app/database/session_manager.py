import functools
import uuid

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, OperationalError


def _with_reconnect(fn):
    """Retry a DB call once after disposing the connection pool.

    pool_pre_ping is supposed to catch a connection Neon has silently
    closed server-side, but not every driver/SQLAlchemy version reports
    every disconnect message in a way pre_ping recognizes (this exact
    "SSL connection has been closed unexpectedly" case slips through).
    As a belt-and-braces fix: if a call fails with an operational/DBAPI
    error, drop the whole pool (so no other stale connections linger)
    and retry once with a guaranteed-fresh connection. If it fails again,
    the error is real and gets raised.
    """
    @functools.wraps(fn)
    def wrapper(self, *args, **kwargs):
        try:
            return fn(self, *args, **kwargs)
        except (OperationalError, DBAPIError):
            self.engine.dispose()
            return fn(self, *args, **kwargs)
    return wrapper


class SessionManager:

    def __init__(self, engine):
        self.engine = engine
        # NOTE: create_table() is intentionally NOT called here.
        # Doing a blocking DB call inside __init__ means it fires at
        # *import time* (as soon as `app.api.chat` is imported), before
        # Uvicorn has even finished starting up. If Neon is slow to wake
        # (cold start) or unreachable, the whole process appears to hang
        # with no log output. Call init() explicitly from the FastAPI
        # lifespan handler instead, where it runs after startup logging
        # has begun and any failure is clearly attributable.

    def init(self):
        """Run one-time setup (table creation). Call this from the
        app's lifespan startup, not from __init__."""
        self.create_table()

    @_with_reconnect
    def create_table(self):
        with self.engine.begin() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    thread_id TEXT PRIMARY KEY,
                    title TEXT,
                    created_at TIMESTAMP DEFAULT NOW(),
                    last_message TEXT,
                    updated_at TIMESTAMP DEFAULT NOW()
                );
            """))

    @_with_reconnect
    def update_title(self, thread_id: str, title: str):

        with self.engine.begin() as conn:

            conn.execute(
                text("""
                    UPDATE chat_sessions
                    SET title = :title
                    WHERE thread_id = :thread_id
                """),
                {
                    "title": title,
                    "thread_id": thread_id
                }
            )

    @_with_reconnect
    def create_session(self, title: str):

        thread_id = str(uuid.uuid4())

        with self.engine.begin() as conn:

            conn.execute(
                text("""
                    INSERT INTO chat_sessions(
                        thread_id,
                        title
                    )
                    VALUES(
                        :thread_id,
                        :title
                    )
                """),
                {
                    "thread_id": thread_id,
                    "title": title
                }
            )

        return thread_id

    @_with_reconnect
    def list_sessions(self):

        with self.engine.begin() as conn:

            result = conn.execute(
                text("""
                    SELECT
                        thread_id,
                        title,
                        last_message,
                        created_at,
                        updated_at
                    FROM chat_sessions
                    ORDER BY updated_at DESC NULLS LAST
                """)
            )

            return result.fetchall()

    @_with_reconnect
    def get_session(self, thread_id: str):

        with self.engine.begin() as conn:

            result = conn.execute(
                text("""
                    SELECT *
                    FROM chat_sessions
                    WHERE thread_id = :thread_id
                """),
                {
                    "thread_id": thread_id
                }
            )

            return result.fetchone()

    @_with_reconnect
    def delete_session(
        self,
        thread_id: str
    ):

        with self.engine.begin() as conn:

            conn.execute(
                text("""
                    DELETE FROM chat_sessions
                    WHERE thread_id = :thread_id
                """),
                {
                    "thread_id": thread_id
                }
            )

    @_with_reconnect
    def update_activity(
        self,
        thread_id: str,
        last_message: str
    ):

        with self.engine.begin() as conn:

            conn.execute(
                text("""
                UPDATE chat_sessions
                SET
                    last_message = :last_message,
                    updated_at = CURRENT_TIMESTAMP
                    WHERE thread_id = :thread_id
            """),
            {
                "thread_id": thread_id,
                "last_message": last_message
            }
        )