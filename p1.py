import requests

API_KEY = "5ORWi2gHH3X7DEV3YMU2xRVbBcnGMnUMG5cIxpSg"  # Замените на ваш реальный API-ключ
URL = "https://api.cloudflare.com/client/v4/accounts"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

response = requests.get(URL, headers=headers)

if response.status_code == 200:
    data = response.json()
    print(data)
else:
    print(f"Ошибка: {response.status_code}, {response.text}")