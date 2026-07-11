class ChatSession(Base):
    __tablename__ = "chat_sessions"

    thread_id = Column(String, primary_key=True)
    title = Column(String)