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
    
    def get_history(self,thread_id: str):

        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }

        state = workflow.get_state(
            config
        )

        return state.values.get(
            "messages",
            []
        )


    def stream_message(
        self,
        thread_id: str,
        message: str
    ):

        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }

        for chunk in workflow.stream(
            {
                "messages": [
                    HumanMessage(
                        content=message
                    )
                ]
            },
            config=config,
            stream_mode="messages"
        ):

            yield chunk


chat_service = ChatService()