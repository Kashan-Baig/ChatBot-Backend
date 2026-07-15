import json

from fastapi import (
    APIRouter,
    HTTPException
)
from fastapi.responses import StreamingResponse

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
            "last_message": row.last_message,
            "created_at": row.created_at,
            "updated_at": row.updated_at
        }
        for row in data
    ]

@router.post("/message")
async def send_message(request: ChatRequest):

    session = session_manager.get_session(
        request.thread_id
    )

    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )

    response = await chat_service.send_message(
        request.thread_id,
        request.message
    )

    session_manager.update_activity(
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

@router.get("/history/{thread_id}")
async def get_history(thread_id: str):

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

    messages = await chat_service.get_history(
        thread_id
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

@router.get("/{thread_id}")
def get_chat(thread_id: str):

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

@router.put("/{thread_id}/rename")
def rename_chat(thread_id: str,request: RenameSessionRequest):

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

@router.delete("/{thread_id}")
def delete_chat(thread_id: str):

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

@router.post("/message/stream")
async def stream_message(request: ChatRequest):

    session = session_manager.get_session(
        request.thread_id
    )

    if not session:

        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )

    async def generate():

        full_response = ""

        try:
            async for token in chat_service.stream_message(
                request.thread_id,
                request.message
            ):
                full_response += token
                # SSE framing: each event is its own "data:" line.
                # Sending JSON (not raw text) lets the client tell
                # content apart from control/error events cleanly.
                yield f"data: {json.dumps({'content': token})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            return

        # Persist activity/title exactly like the non-streaming route does,
        # now that we have the full assembled response.
        session_manager.update_activity(
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

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            # Prevents nginx (and some other reverse proxies) from
            # buffering the response, which is a common cause of
            # streaming showing up as one big chunk in production.
            "X-Accel-Buffering": "no",
        },
    )