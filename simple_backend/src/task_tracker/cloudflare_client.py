import requests
import os
from dotenv import load_dotenv

load_dotenv()

class CloudflareClient:
    def __init__(self):
        self.api_key = os.getenv("CLOUDFLARE_API_KEY")
        self.api_url = "https://api.cloudflare.com/client/v4/accounts/57ee70b4582d2b003a94cd3e16051019/ai/run/@cf/meta/llama-2-7b-chat-int8"
        self.account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
        self.model_name = "@cf/meta/llama-2-7b-chat-int8"

    def get_llm_response(self, prompt: str) -> str:
        """Отправляет запрос в LLM и возвращает ответ."""
        url = self.api_url.format(account_id=self.account_id, model_name=self.model_name)
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        data = {
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ]
        }

        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json().get("result", {}).get("response", "")
        else:
            raise Exception(f"Ошибка при запросе к LLM: {response.status_code}")

