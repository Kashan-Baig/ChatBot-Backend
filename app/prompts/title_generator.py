from app.llm.model import model


def generate_title(user_message: str):

    prompt = f"""
    Generate a short chat title.

    Rules:
    - 3 to 6 words
    - concise
    - describe topic

    User Message:
    {user_message}

    Return only the title.
    """

    response = model.invoke(prompt)

    return response.content.strip()