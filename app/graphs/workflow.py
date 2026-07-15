import os
from dotenv import load_dotenv
load_dotenv()

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool
from psycopg.rows import dict_row

from app.graphs.state import ChatState
from app.graphs.nodes import chat

DATABASE_URL = os.getenv("DATABASE_URL")

_graph = StateGraph(ChatState)
_graph.add_node("chat", chat)
_graph.add_edge(START, "chat")
_graph.add_edge("chat", END)

# Populated by init_workflow() during app startup (see main.py lifespan below)
workflow = None
_pool = None


async def init_workflow():
    """
    Must be awaited once, at app startup, inside a running event loop
    (e.g. from a FastAPI lifespan handler).

    IMPORTANT: this uses a real connection *pool* (psycopg_pool), not
    AsyncPostgresSaver.from_conn_string(). from_conn_string() opens a
    single raw connection and holds it open for the app's entire
    lifetime with no health check and no reconnect logic. Neon (like
    most managed/serverless Postgres) silently closes idle connections
    after a while, so that single connection eventually goes stale and
    every query after that fails with:
        psycopg.OperationalError: consuming input failed:
        SSL connection has been closed unexpectedly
    A pool with `check=AsyncConnectionPool.check_connection` validates
    (and transparently replaces) a connection before handing it to a
    caller, so a server-side close never surfaces as a 500.
    """
    global workflow, _pool

    _pool = AsyncConnectionPool(
        conninfo=DATABASE_URL,
        min_size=1,
        max_size=10,
        kwargs={
            "autocommit": True,
            "prepare_threshold": 0,
            "row_factory": dict_row,
        },
        check=AsyncConnectionPool.check_connection,
        # Proactively recycle connections that have sat idle a while
        # instead of waiting to discover they're dead on next use.
        max_idle=300,
        open=False,
    )
    await _pool.open()

    checkpointer = AsyncPostgresSaver(_pool)
    await checkpointer.setup()

    workflow = _graph.compile(checkpointer=checkpointer)
    return workflow


async def close_workflow():
    """Call from the same lifespan handler on shutdown."""
    global _pool
    if _pool is not None:
        await _pool.close()