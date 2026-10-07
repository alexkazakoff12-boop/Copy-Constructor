import sqlglot
from sqlglot import exp

ALLOWED_COLUMNS = {
    "admissions_summary": {"admission_year", "program_id", "status", "total"},
    "programs": {"id", "name"},
    "grade_summary": {
        "course", "year", "semester", "grades_count", "average_grade"
    },
}
ALLOWED_FUNCTIONS = {"Sum", "Avg", "Count", "Round", "Coalesce", "Cast"}
FORBIDDEN = (
    exp.Subquery, exp.CTE, exp.Union, exp.Intersect, exp.Except, exp.Offset
)


class UnsafeSQL(ValueError):
    pass


def validate_sql(raw_sql: str) -> str:
    if not isinstance(raw_sql, str) or not raw_sql.strip() or len(raw_sql) > 4000:
        raise UnsafeSQL("Пустой или слишком длинный SQL")

    try:
        statements = sqlglot.parse(raw_sql, read="postgres")
    except sqlglot.errors.SqlglotError as exc:
        raise UnsafeSQL("Ошибка синтаксиса SQL") from exc

    if len(statements) != 1 or not isinstance(statements[0], exp.Select):
        raise UnsafeSQL("Разрешён только один SELECT")

    query = statements[0]
    if query.args.get("with_") or query.args.get("into") or query.args.get("locks"):
        raise UnsafeSQL("CTE, SELECT INTO и блокировки запрещены")
    if query.args.get("limit"):
        raise UnsafeSQL("LIMIT добавляет сервер")
    if any(isinstance(node, FORBIDDEN) for node in query.walk()):
        raise UnsafeSQL("Вложенные запросы запрещены")
    if any(isinstance(node, exp.Star) for node in query.walk()):
        raise UnsafeSQL("SELECT * запрещён")
    for node in query.walk():
        if (
            isinstance(node, exp.Func)
            and not isinstance(node, exp.Connector)
            and type(node).__name__ not in ALLOWED_FUNCTIONS
        ):
            raise UnsafeSQL(f"Функция не разрешена: {type(node).__name__}")

    tables = list(query.find_all(exp.Table))
    if not tables:
        raise UnsafeSQL("Нужна разрешённая таблица")

    aliases = {}
    for table in tables:
        name = table.name.casefold()
        if (
            name not in ALLOWED_COLUMNS
            or table.db not in ("", "public")
            or table.catalog
        ):
            raise UnsafeSQL("Таблица не разрешена")
        alias = table.alias_or_name.casefold()
        if alias in aliases:
            raise UnsafeSQL("Повторный псевдоним таблицы")
        aliases[alias] = name

    output_aliases = {
        item.alias.casefold() for item in query.expressions if item.alias
    }
    for column in query.find_all(exp.Column):
        name = column.name.casefold()
        if column.table:
            table = aliases.get(column.table.casefold())
            if table is None or name not in ALLOWED_COLUMNS[table]:
                raise UnsafeSQL("Недоступный столбец")
        elif name not in output_aliases and not any(
            name in ALLOWED_COLUMNS[table] for table in aliases.values()
        ):
            raise UnsafeSQL("Недоступный столбец")

    return query.limit(50).sql(dialect="postgres")