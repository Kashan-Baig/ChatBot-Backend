from fastapi import APIRouter

from app.database.connection import engine
from app.database.session_manager import SessionManager

from app.prompts.title_generator import (
    generate_title
)

from app.services.chat_service import (
    chat_service
)

from app.schemas.chat import (
    ChatRequest
)

router = APIRouter()

session_manager = SessionManager(engine)

@router.post("/new")
def new_chat():

    thread_id = session_manager.create_session(
        "New Chat"
    )

    return {
        "thread_id": thread_id,
        "title": "New Chat"
    }

@router.get("/sessions")
def sessions():

    data = (
        session_manager
        .list_sessions()
    )

    return [
        {
            "thread_id": row.thread_id,
            "title": row.title,
            "created_at": row.created_at
        }
        for row in data
    ]

@router.post("/message")
def send_message(request: ChatRequest):

    session = session_manager.get_session(
        request.thread_id
    )

    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )

    response = chat_service.send_message(
        request.thread_id,
        request.message
    )

    if session.title == "New Chat":

        title = generate_title(
            request.message
        )

        session_manager.update_title(
            request.thread_id,
            title
        )

    return {
        "thread_id": request.thread_id,
        "response": response
    }