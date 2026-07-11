import uuid
from sqlalchemy import text


class SessionManager:

    def __init__(self, engine):
        self.engine = engine
        self.create_table()

    def create_table(self):
        with self.engine.begin() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    thread_id TEXT PRIMARY KEY,
                    title TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """))

    def update_title(self,thread_id: str,title: str):

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

    def list_sessions(self):

        with self.engine.begin() as conn:

            result = conn.execute(
                text("""
                    SELECT
                        thread_id,
                        title,
                        created_at
                    FROM chat_sessions
                    ORDER BY created_at DESC
                """)
            )

            return result.fetchall()