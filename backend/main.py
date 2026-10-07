import json
import logging
import os
import re
from contextlib import asynccontextmanager

import asyncpg
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel, Field

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OLLAMA_URL = os.environ.get("OLLAMA_URL", "").rstrip("/")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "")

# Только заранее подготовленная агрегированная витрина и справочник программ.
SQL = """
SELECT p.name AS program, s.admission_year AS year,
       s.status, SUM(s.total)::integer AS applications
FROM public.admissions_summary AS s
JOIN public.programs AS p ON p.id = s.program_id
WHERE ($1::text IS NULL OR p.name = $1)
  AND ($2::integer IS NULL OR s.admission_year = $2)
  AND ($3::text IS NULL OR s.status = $3)
GROUP BY p.name, s.admission_year, s.status
ORDER BY s.admission_year DESC, p.name, s.status
LIMIT 101
"""
STATUSES = {"подано", "зачислен", "отклонено"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.pool = await asyncpg.create_pool(
        os.environ["DATABASE_URL"], min_size=1, max_size=5, command_timeout=5,
    )
    app.state.http = httpx.AsyncClient(timeout=httpx.Timeout(90.0, connect=5.0))
    try:
        yield
    finally:
        await app.state.http.aclose()
        await app.state.pool.close()


app = FastAPI(lifespan=lifespan)


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)


def result(answer=None, sql=None, columns=None, rows=None, error=None):
    return {
        "answer": answer, "sql": sql, "columns": columns or [],
        "rows": rows or [], "error": error,
    }


def mentions_program(question: str, program: str, programs: list[str]) -> bool:
    question = question.casefold()
    if program.casefold() in question:
        return True
    # Учитываем падежи: «Экономика» → «Экономику», но не используем
    # общие части названий вроде «Прикладная» для выбора программы.
    stems = {
        word[:5].casefold()
        for word in re.findall(r"[^\W\d_]+", program)
        if len(word) >= 6
    }
    for other in programs:
        if other == program:
            continue
        stems -= {
            word[:5].casefold()
            for word in re.findall(r"[^\W\d_]+", other)
            if len(word) >= 6
        }
    return any(stem in question for stem in stems)


async def extract_filters(question: str, programs: list[str]):
    prompt = (
        "Ты разбираешь вопрос к статистике приёма в вуз. "
        "Верни ТОЛЬКО JSON с полями: "
        '"relevant" (boolean), "program" (строка или null), '
        '"year" (число или null), "status" (строка или null). '
        "Вопросы про оценки, преподавателей, студентов и персональные данные: relevant=false. "
        "Для вопроса про заявления используй status=подано; про зачисление — "
        "status=зачислен; про отклонения — status=отклонено. "
        "Если статус не назван, оставь null. "
        "Названия программ выбирай строго из списка; не угадывай год. "
        f"Программы: {json.dumps(programs, ensure_ascii=False)}. "
        f"Вопрос: {json.dumps(question, ensure_ascii=False)}"
    )
    response = await app.state.http.post(
        f"{OLLAMA_URL}/api/chat",
        json={
            "model": OLLAMA_MODEL,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0},
            "messages": [{"role": "user", "content": prompt}],
        },
    )
    response.raise_for_status()
    data = json.loads(response.json()["message"]["content"])
    if not isinstance(data, dict):
        raise ValueError("unsupported question")

    names = {name.casefold(): name for name in programs}
    raw_program = data.get("program")
    if raw_program is not None:
        if not isinstance(raw_program, str) or raw_program.casefold() not in names:
            raise ValueError("unknown program")
        program = names[raw_program.casefold()]
        if not mentions_program(question, program, programs):
            # Не подставляем выдуманное моделью название программы.
            raise ValueError("program not found in question")
    else:
        program = None

    year = data.get("year")
    if isinstance(year, str) and re.fullmatch(r"20\d{2}", year):
        year = int(year)
    if year is not None and (
        type(year) is not int or year < 2020 or year > 2030
        or not re.search(rf"(?<!\d){year}(?!\d)", question)
    ):
        raise ValueError("invalid year")

    status = data.get("status")
    if status is not None and status not in STATUSES:
        raise ValueError("invalid status")
    lowered = question.casefold()
    if "зачисл" in lowered:
        status = "зачислен"
    elif "отклон" in lowered:
        status = "отклонено"
    elif "заявлен" in lowered or "подан" in lowered:
        status = "подано"
    return program, year, status


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/chat")
async def chat(request: ChatRequest):
    if not OLLAMA_URL or not OLLAMA_MODEL:
        return result(error="Укажите OLLAMA_URL и OLLAMA_MODEL в backend/.env.")

    try:
        async with app.state.pool.acquire() as conn:
            async with conn.transaction(readonly=True):
                await conn.execute("SET LOCAL statement_timeout = '3000ms'")
                programs = await conn.fetch("SELECT name FROM public.programs ORDER BY name LIMIT 100")
        filters = await extract_filters(request.question, [row["name"] for row in programs])
    except ValueError:
        return result(error="Пока поддерживаются вопросы по агрегированной статистике приёма.")
    except (httpx.HTTPError, KeyError, json.JSONDecodeError):
        logger.exception("Ollama request failed")
        return result(error="Не удалось получить ответ от модели на втором ноутбуке.")
    except Exception:
        logger.exception("Database setup failed")
        return result(error="Не удалось прочитать справочник программ из базы данных.")

    try:
        async with app.state.pool.acquire() as conn:
            async with conn.transaction(readonly=True):
                await conn.execute("SET LOCAL statement_timeout = '3000ms'")
                records = await conn.fetch(SQL, *filters)
    except Exception:
        logger.exception("Database query failed")
        return result(error="Не удалось выполнить запрос к базе данных.")

    if len(records) > 100:
        return result(error="Слишком широкий вопрос. Укажите программу или год.")
    if not records:
        return result(answer="По этому условию данных нет.", sql=SQL)

    rows = [[r["program"], r["year"], r["status"], r["applications"]] for r in records]
    total = sum(r["applications"] for r in records)
    return result(
        answer=f"По доступным агрегированным данным: {total} записей. Детали в таблице.",
        sql=SQL,
        columns=["Программа", "Год", "Статус", "Количество"],
        rows=rows,
    )
