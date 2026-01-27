from typing import Any, List, Dict, Optional
from openai import OpenAI
from pathlib import Path
import json


class LLMUtil:
    def __init__(self, client: OpenAI, prompt_template: str) -> None:
        self.client = client
        self.prompt_path = Path(prompt_template)

        self.system_prompt = self._fetch_prompt()
        if self.system_prompt is None:
            raise ValueError("System prompt could not be loaded.")

        self.messages: List[Dict[str, str]] = [
            {"role": "system", "content": self.system_prompt}
        ]

    def _fetch_prompt(self) -> Optional[str]:
        data = self._read_prompt_file(self.prompt_path)
        if not data:
            return None
        return data.get("system_prompt")

    def _read_prompt_file(self, file: Path) -> Optional[dict]:
        if not file.exists():
            raise FileNotFoundError(f"Prompt file not found: {file}")

        if file.suffix != ".json":
            raise ValueError("Prompt file must be a JSON file")

        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)



    def _get_usage_stats(self, response: Any) -> str:
        usage_dict = response.usage.to_dict()
        usage_stats = f"""
        {'-' * 50}
        Total Tokens: {usage_dict['total_tokens']}
        Prompt Tokens: {usage_dict['prompt_tokens']}
        Completion Tokens: {usage_dict['completion_tokens']}
        {'-' * 50}
        """
        return usage_stats
    

    def chat(self, user_input: str, model: str = "local-model") -> str:
        self.messages.append({"role": "user", "content": user_input})

        response = self.client.chat.completions.create(
            model=model,
            messages=self.messages,
        )

        reply = response.choices[0].message.content
        usage_stats = self._get_usage_stats(response)
        self.messages.append({"role": "assistant", "content": reply})
        return reply, usage_stats






client = OpenAI(
    base_url="http://localhost:1234/v1"
)


llm_client = LLMUtil(client, r"prompts\v1.json")

while True:
    user_input = input("User: ")
    if user_input.lower() == "exit":
        break
    reply, token_stats = llm_client.chat(user_input)
    print(f"Assistant: {reply}")
    print("\nUsage Stats:\n", token_stats)