from langchain_core.messages import HumanMessage

from app.graphs.workflow import workflow


class ChatService:

    def send_message(
        self,
        thread_id: str,
        message: str
    ):

        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }

        result = workflow.invoke(
            {
                "messages": [
                    HumanMessage(
                        content=message
                    )
                ]
            },
            config=config
        )

        return result["messages"][-1].content


chat_service = ChatService()