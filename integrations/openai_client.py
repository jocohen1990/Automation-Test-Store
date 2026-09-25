import os

from dotenv import load_dotenv
from openai import OpenAI


def get_openai_client():
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY must be set in the environment."
        )

    return OpenAI(api_key=api_key)


def ask_openai(prompt: str) -> str:
    client = get_openai_client()

    response = client.responses.create(
        model="gpt-5.6-luna",
        input=prompt,
    )

    return response.output_text

# Using GPT-5.6 Luna here because this is a development/test project where you're going to make a lot of relatively small API calls. OpenAI currently describes Luna as its cost-sensitive, high-volume model.