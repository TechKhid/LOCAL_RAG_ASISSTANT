from openai import OpenAI
from pprint import pprint

client = OpenAI(
    base_url="http://localhost:1234/v1"
)

exit_ = False
context = []
while not exit_:
    try:
        user_input = input("User: ")

        if user_input.lower() == "exit":
            exit_ = True
            pprint("Exiting...")
            break

        context.append(f"User: {user_input}")
        response = client.chat.completions.create(
            model="local-model",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant.",
                },
                {
                    "role": "user",
                    "content": str(context),
                }
            ],
        )
        reply = f"Assistant: {response.choices[0].message.content}\n"
        pprint(reply)
        context.append(reply)
        
    except Exception as e:      
        print(e)
        exit_ = True




#