import json
import re

SQL = """
SELECT course, year, semester, grades_count, average_grade
FROM public.grade_summary
WHERE course = $1 AND year = $2
ORDER BY semester
LIMIT 8
"""


async def grade_chat(question, pool, http, ollama_url, ollama_model):
    def error(message):
        return {
            "answer": None, "sql": None,
            "columns": [], "rows": [], "error": message,
        }

    match = re.search(r"(?<!\d)20\d{2}(?!\d)", question)
    if not match:
        return error("Укажите учебный год, например 2025.")
    year = int(match.group())

    try:
        async with pool.acquire() as conn:
            async with conn.transaction(readonly=True):
                await conn.execute("SET LOCAL statement_timeout = '3000ms'")
                records = await conn.fetch(
                    "SELECT DISTINCT course FROM public.grade_summary ORDER BY course"
                )
        courses = [row["course"] for row in records]

        prompt = (
            "Выбери курс из списка. Ответь только JSON вида "
            '{"course":"точное название курса или null"}. '
            f"Курсы: {json.dumps(courses, ensure_ascii=False)}. "
            f"Вопрос: {json.dumps(question, ensure_ascii=False)}"
        )
        response = await http.post(
            f"{ollama_url}/api/chat",
            json={
                "model": ollama_model,
                "stream": False,
                "format": "json",
                "options": {"temperature": 0},
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        response.raise_for_status()
        suggested = json.loads(response.json()["message"]["content"]).get("course")

        # Модель может склонять название. Выбираем только курс из БД,
        # который упоминается в вопросе.
        mentioned = [
            course for course in courses
            if any(
                word[:3 if len(word) <= 4 else 5] in question.casefold()
                for word in re.findall(r"[^\W\d_]+", course.casefold())
                if len(word) >= 4
            )
        ]
        if len(mentioned) != 1:
            return error("Уточните название курса из базы данных.")
        course = mentioned[0]
        if suggested not in (None, course):
            # Название от модели не подставляем в SQL.
            pass

        async with pool.acquire() as conn:
            async with conn.transaction(readonly=True):
                await conn.execute("SET LOCAL statement_timeout = '3000ms'")
                rows_db = await conn.fetch(SQL, course, year)
    except Exception:
        return error("Не удалось получить статистику оценок.")

    if not rows_db:
        return {
            "answer": "По этому условию данных нет.", "sql": SQL,
            "columns": [], "rows": [], "error": None,
        }

    count = sum(row["grades_count"] for row in rows_db)
    average = sum(
        float(row["average_grade"]) * row["grades_count"]
        for row in rows_db
    ) / count
    rows = [
        [
            row["course"], row["year"], row["semester"],
            float(row["average_grade"]), row["grades_count"],
        ]
        for row in rows_db
    ]
    return {
        "answer": (
            f"Средний балл по {course} за {year} год: {average:.2f} "
            f"(по {count} оценкам в доступных группах)."
        ),
        "sql": SQL,
        "columns": ["Курс", "Год", "Семестр", "Средний балл", "Оценок"],
        "rows": rows,
        "error": None,
    }