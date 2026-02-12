import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv

# 1. 配置环境
load_dotenv()
# 记得在同级目录的 .env 文件里写上 GOOGLE_API_KEY=你的密钥
if not os.getenv("GOOGLE_API_KEY"):
    print("警告: 未找到 GOOGLE_API_KEY")

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# 2. 定义模型和人设
model = genai.GenerativeModel(
    'gemini-2.5-flash',
    system_instruction="你是一个同济大学SITP项目的AI德语助教。请用德语回答，括号内给出中文解释，并指出用户的语法错误。如果用户说中文，请引导通过德语表达。"
)
chat = model.start_chat(history=[])

app = FastAPI()

# 3. 允许跨域（必须加，否则前端报错）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. 定义数据格式
class ChatRequest(BaseModel):
    message: str

# 5. 核心接口
@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    print(f"收到前端消息: {request.message}") # 终端打印，方便你调试
    
    try:
        response = chat.send_message(request.message)
        return {"reply": response.text}
    except Exception as e:
        print(f"Gemini调用失败: {e}")
        return {"reply": "Entschuldigung, ich habe ein Problem. (AI出错了)"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)