from fastapi import (
    APIRouter,
    HTTPException
)

from app.database.connection import engine
from app.database.session_manager import SessionManager

from app.prompts.title_generator import (
    generate_title
)

from app.services.chat_service import (
    chat_service
)

from app.schemas.chat import (
    ChatRequest,
    RenameSessionRequest
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

@router.get(
    "/history/{thread_id}"
)
def get_history(
    thread_id: str
):

    session = (
        session_manager.get_session(
            thread_id
        )
    )

    if not session:

        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )

    messages = (
        chat_service.get_history(
            thread_id
        )
    )

    history = []

    for msg in messages:

        role = (
            "assistant"
            if msg.type == "ai"
            else "user"
        )

        history.append(
            {
                "role": role,
                "content": msg.content
            }
        )

    return {
        "thread_id": thread_id,
        "messages": history
    }

@router.get(
    "/{thread_id}"
)
def get_chat(
    thread_id: str
):

    session = (
        session_manager.get_session(
            thread_id
        )
    )

    if not session:

        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )

    return {
        "thread_id": session.thread_id,
        "title": session.title,
        "created_at": session.created_at
    }

@router.put(
    "/{thread_id}/rename"
)
def rename_chat(
    thread_id: str,
    request: RenameSessionRequest
):

    session = (
        session_manager.get_session(
            thread_id
        )
    )

    if not session:

        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )

    session_manager.update_title(
        thread_id,
        request.title
    )

    return {
        "message": "Chat renamed"
    }

@router.delete(
    "/{thread_id}"
)
def delete_chat(
    thread_id: str
):

    session = (
        session_manager.get_session(
            thread_id
        )
    )

    if not session:

        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )

    session_manager.delete_session(
        thread_id
    )

    return {
        "message": "Chat deleted"
    }