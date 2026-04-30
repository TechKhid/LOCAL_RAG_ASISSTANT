from openai import OpenAI
from src.config import LLM_BASE_URL

client = OpenAI(base_url=LLM_BASE_URL, api_key="local-not-required")

messages = [
    {"role": "system", "content": "You are a helpful assistant."}
]

while True:
    user_input = input("User: ")

    if user_input.lower() == "exit":
        print("Exiting...")
        break

    messages.append({"role": "user", "content": user_input})

    response = client.chat.completions.create(
        model="local-model",
        messages=messages,
    )

    assistant_reply = response.choices[0].message.content
    print(f"Assistant: {assistant_reply}\n")

    messages.append({"role": "assistant", "content": assistant_reply})
