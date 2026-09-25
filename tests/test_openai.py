from integrations.openai_client import ask_openai


def test_openai_connection():
    response = ask_openai(
        "Respond with exactly: OpenAI API connection successful."
    )

    assert response

    print("\nOpenAI API connection test completed successfully.")
    print("Response:", response)