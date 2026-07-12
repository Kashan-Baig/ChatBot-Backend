from datetime import datetime
from sqlalchemy import DateTime

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    thread_id = Column(String, primary_key=True)
    title = Column(String, nullable=False)

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    last_message = Column(
        String,
        nullable=True
    )