from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.chat import router, session_manager

from app.graphs.workflow import (
    init_workflow,
    close_workflow
)
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs the (blocking, but now clearly logged) chat_sessions table
    # creation here, after Uvicorn has started logging, instead of at
    # module-import time.
    print("[startup] creating chat_sessions table (sync engine)...")
    session_manager.init()
    print("[startup] chat_sessions table ready.")

    print("[startup] connecting AsyncPostgresSaver + compiling workflow...")
    await init_workflow()
    print("[startup] workflow ready. App is up.")

    yield

    print("[shutdown] closing checkpointer connection...")
    await close_workflow()

app = FastAPI(
    title="Chatbot API",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    router,
    prefix="/api/chat",
    tags=["Chat"]
)