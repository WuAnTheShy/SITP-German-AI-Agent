import os
import requests
import json
from dotenv import load_dotenv

load_dotenv("../.env")

api_key = os.getenv("QWEN_API_KEY", "")
print(f"API key prefix: {api_key[:10]}...")

url = "https://dashscope.aliyuncs.com/api/v1/services/rerank/text-rerank/text-rerank"

payload = {
    "model": "gte-rerank",
    "input": {
        "query": "被动语态怎么构造？",
        "documents": [
            "Ich bin nicht stark genug, diesen Koffer zu heben.",
            "Das Passiv wird mit dem Hilfsverb werden und dem Partizip II gebildet.",
            "die Frucht, die Früchte n fruit",
        ],
    },
    "parameters": {
        "return_documents": True,
        "top_n": 3,
    },
}

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
}

resp = requests.post(url, json=payload, headers=headers, timeout=30)
print(f"\nStatus: {resp.status_code}")
print(f"Response:\n{json.dumps(resp.json(), indent=2, ensure_ascii=False)}")