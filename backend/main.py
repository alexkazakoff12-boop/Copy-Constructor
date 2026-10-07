import logging
import os
import re
from contextlib import asynccontextmanager

import asyncpg
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel, Field

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SQL = """
SELECT p.name AS program, s.admission_year AS year,
       SUM(s.total)::integer AS applications
FROM public.admissions_summary AS s
JOIN public.programs AS p ON p.id = s.program_id
WHERE p.name = $1 AND s.admission_year = $2 AND s.status = 'подано'
GROUP BY p.name, s.admission_year
LIMIT 100
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.pool = await asyncpg.create_pool(
        os.environ["DATABASE_URL"],
        min_size=1,
        max_size=5,
        command_timeout=5,
    )
    try:
        yield
    finally:
        await app.state.pool.close()


app = FastAPI(lifespan=lifespan)


class ChatRequest(BaseModel):
    question: str = Field(min_length=1)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/chat")
async def chat(request: ChatRequest):
    question = request.question.casefold()
    year_match = re.search(r"\b20\d{2}\b", question)

    if "экономик" not in question or "заявлен" not in question or not year_match:
        return {
            "answer": None,
            "sql": None,
            "columns": [],
            "rows": [],
            "error": "Пока поддерживается вопрос о заявлениях на Экономику с указанием года.",
        }

    year = int(year_match.group())
    try:
        async with app.state.pool.acquire() as conn:
            async with conn.transaction(readonly=True):
                await conn.execute("SET LOCAL statement_timeout = '3000ms'")
                row = await conn.fetchrow(SQL, "Экономика", year)
    except Exception:
        logger.exception("Database query failed")
        return {
            "answer": None,
            "sql": SQL,
            "columns": [],
            "rows": [],
            "error": "Не удалось выполнить запрос к базе данных.",
        }

    if row is None:
        return {
            "answer": "По этому условию данных нет.",
            "sql": SQL,
            "columns": [],
            "rows": [],
            "error": None,
        }

    return {
        "answer": f"На Экономику в {year} году подано {row['applications']} заявлений.",
        "sql": SQL,
        "columns": ["Программа", "Год", "Заявления"],
        "rows": [[row["program"], row["year"], row["applications"]]],
        "error": None,
    }