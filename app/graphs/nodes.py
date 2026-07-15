from langchain_core.messages import SystemMessage
from app.prompts.system_prompt import SYSTEM_PROMPT
from app.llm.model import model


async def chat(state):

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        *state["messages"]
    ]

    full_message = None

    async for chunk in model.astream(messages):
        full_message = chunk if full_message is None else full_message + chunk

    return {
        "messages": [full_message]
    }