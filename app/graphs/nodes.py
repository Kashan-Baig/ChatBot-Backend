from langchain_core.messages import SystemMessage, AIMessage
from app.prompts.system_prompt import SYSTEM_PROMPT
from app.llm.model import model


def chat(state):

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        *state["messages"]
    ]

    response = "".join(chunk.content for chunk in model.stream(messages))

    return {
        "messages": [AIMessage(content=response)]
    }