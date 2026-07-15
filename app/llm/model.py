from langchain_groq import ChatGroq

model = ChatGroq(
    model="openai/gpt-oss-120b",
    streaming=True,
)