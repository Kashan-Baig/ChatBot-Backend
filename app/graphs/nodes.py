from langchain_core.messages import SystemMessage
from app.prompts.system_prompt import SYSTEM_PROMPT
from app.llm.model import model


def chat(state):

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        *state["messages"]
    ]

    response = model.invoke(messages)

    return {
        "messages": [response]
    }