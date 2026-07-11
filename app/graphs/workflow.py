import os
from dotenv import load_dotenv
load_dotenv()
from langgraph.graph import StateGraph
from langgraph.graph import START, END
from langgraph.checkpoint.postgres import PostgresSaver

from app.graphs.state import ChatState
from app.graphs.nodes import chat


graph = StateGraph(ChatState)

graph.add_node("chat", chat)

graph.add_edge(START, "chat")
graph.add_edge("chat", END)


DATABASE_URL = os.getenv("DATABASE_URL")

checkpointer_cm = PostgresSaver.from_conn_string(
    DATABASE_URL
)

checkpointer = checkpointer_cm.__enter__()

checkpointer.setup()

workflow = graph.compile(
    checkpointer=checkpointer
)