from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI()


class ChatRequest(BaseModel):
    question: str = Field(min_length=1)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/chat")
async def chat(request: ChatRequest):
    return {
        "answer": f"Тестовый режим: получен вопрос «{request.question}».",
        "sql": None,
        "columns": [],
        "rows": [],
        "error": None,
    }
