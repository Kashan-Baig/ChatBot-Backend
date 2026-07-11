from fastapi import FastAPI

from app.api.chat import router


app = FastAPI(
    title="Chatbot API"
)

app.include_router(
    router,
    prefix="/api/chat",
    tags=["Chat"]
)