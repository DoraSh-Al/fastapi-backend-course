import requests
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import json

app = FastAPI()

# Конфигурация API
FILE_STORAGE_URL = "https://example.com/api/files"
JSONBIN_API_KEY = "$2a$10$bLZ2aNVqrtMnHub27kLYvuG3E96w2QyE2bxl3CO22YcPWMY8I91zy"
JSONBIN_URL = "https://api.jsonbin.io/v3/b/67d01f2d8561e97a50e9e783"
LLM_API_URL = "https://api.cloudflare.com/client/v4/accounts/57ee70b4582d2b003a94cd3e16051019/ai/run/@cf/meta/llama-3.1-8b-instruct"
LLM_API_TOKEN = "0ukQ8LBkocp8QrUFvlhLcz8qQ2q0FUGXPbMGi2JI"

# Класс для работы с файлами
class FileStorageClient:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, headers: Optional[Dict] = None) -> Dict:
        """Универсальный метод для выполнения HTTP-запросов."""
        url = f"{self.base_url}/{endpoint}"
        headers = headers or {}
        response = requests.request(method, url, json=data, headers=headers)
        if response.status_code in [200, 201]:
            return response.json()
        elif response.status_code == 404:
            raise HTTPException(status_code=404, detail="Resource not found")
        raise HTTPException(status_code=response.status_code, detail=f"Request failed: {response.text}")

    def get(self, endpoint: str) -> Dict:
        """Получить файл по ID."""
        return self._make_request("GET", endpoint)

    def post(self, endpoint: str, data: Dict) -> Dict:
        """Загрузить файл."""
        return self._make_request("POST", endpoint, data=data)

    def delete(self, endpoint: str) -> Dict:
        """Удалить файл."""
        return self._make_request("DELETE", endpoint)

# Класс для работы с задачами через JSONBin
class JSONBinStorage:
    def __init__(self, url: str, api_key: str):
        self.url = url
        self.api_key = api_key

    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, headers: Optional[Dict] = None) -> Dict:
        url = f"{self.url}/{endpoint}" if endpoint else self.url
        headers = headers or {"X-Master-Key": self.api_key}
        if method in ["PUT", "POST"]:
            headers["Content-Type"] = "application/json"
        print(f"Making {method} request to {url} with headers {headers} and data {data}")
        response = requests.request(method, url, json=data, headers=headers)
        print(f"Response: {response.status_code} - {response.text}")
        if response.status_code in [200, 201]:
            return response.json()
        elif response.status_code == 404:
            raise HTTPException(status_code=404, detail="Resource not found")
        raise HTTPException(status_code=response.status_code, detail=f"Request failed: {response.text}")

    def load_tasks(self) -> List[Dict]:
        response = self._make_request("GET", "")
        record = response.get("record", {})
        inner_record = record.get("record", {})  # Извлекаем вложенный "record"
        return inner_record.get("tasks", [])  # Берем "tasks" из вложенного record

    def save_tasks(self, tasks: List[Dict]) -> None:
        self._make_request("PUT", "", data={"record": {"tasks": tasks}})

# Класс для работы с LLM API
class LLMClient:
    def __init__(self, api_url: str, api_token: str):
        self.api_url = api_url
        self.headers = {"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"}

    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, headers: Optional[Dict] = None) -> Dict:
        url = f"{self.api_url}/{endpoint}"
        headers = headers or self.headers
        print(f"Making {method} request to {url} with data {data}")
        response = requests.request(method, url, json=data, headers=headers)
        print(f"LLM Response: {response.status_code} - {response.text}")
        if response.status_code in [200, 201]:
            return response.json()
        raise HTTPException(status_code=response.status_code, detail=f"LLM request failed: {response.text}")

    def get_llm_response(self, prompt: str) -> str:
        data = {
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        }
        response = self._make_request("POST", "", data=data)
        return response.get("result", {}).get("response", "No response from LLM")

# Модель задачи
class Task(BaseModel):
    id: Optional[int] = None
    title: str
    description: Optional[str] = None
    completed: bool = False

# Инициализация клиентов
file_client = FileStorageClient(FILE_STORAGE_URL)
storage = JSONBinStorage(JSONBIN_URL, JSONBIN_API_KEY)
llm_client = LLMClient(LLM_API_URL, LLM_API_TOKEN)

# Эндпоинты FastAPI
@app.get("/files/{file_id}")
def get_file(file_id: str):
    return file_client.get(file_id)

@app.post("/files")
def upload_file(file_data: Dict[str, Any]):
    return file_client.post("", file_data)

@app.delete("/files/{file_id}")
def delete_file(file_id: str):
    return file_client.delete(file_id)

@app.post("/llm")
def query_llm(prompt: str):
    return {"response": llm_client.get_llm_response(prompt)}

# Новый эндпоинт для создания задачи
@app.post("/tasks", response_model=Task)
async def create_task(request: Request):
    raw_body = await request.body()
    print(f"Raw request body: {raw_body}")
    body_str = raw_body.decode('utf-8')
    print(f"Decoded body: {body_str}")
    task_data = json.loads(body_str)
    task = Task(**task_data)
    print(f"Parsed task: {task}")
    llm_prompt = f"Explain how to solve the task: {task.title}. {task.description or ''}"
    print(f"LLM Prompt: {llm_prompt}")
    llm_response = llm_client.get_llm_response(llm_prompt)
    print(f"LLM Response: {llm_response}")
    task.description = f"{task.description or ''}\n\nLLM Suggestion: {llm_response}".strip()
    tasks = storage.load_tasks()
    print(f"Loaded tasks: {tasks}")
    tasks.append(task.dict())
    storage.save_tasks(tasks)
    print(f"Saved tasks: {tasks}")
    return task