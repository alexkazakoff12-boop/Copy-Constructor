-- Роль, под которой backend читает БД.
-- Пароль задаётся отдельно и не хранится в Git.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_roles WHERE rolname = 'api_reader'
    ) THEN
        CREATE ROLE api_reader LOGIN;
    END IF;
END
$$;

GRANT CONNECT ON DATABASE bazis TO api_reader;
GRANT USAGE ON SCHEMA public TO api_reader;

-- Статистика приёма без записей отдельных абитуриентов.
CREATE OR REPLACE VIEW public.admissions_summary AS
SELECT
    admission_year,
    program_id,
    status,
    COUNT(*)::integer AS total
FROM public.applications
GROUP BY admission_year, program_id, status
HAVING COUNT(*) >= 5;

-- Средние оценки без кодов отдельных студентов.
CREATE OR REPLACE VIEW public.grade_summary AS
SELECT
    c.name AS course,
    g.academic_year AS year,
    g.semester,
    COUNT(*)::integer AS grades_count,
    ROUND(AVG(g.grade)::numeric, 2) AS average_grade
FROM public.grades AS g
JOIN public.courses AS c ON c.id = g.course_id
GROUP BY c.name, g.academic_year, g.semester
HAVING COUNT(DISTINCT g.student_code) >= 5;

-- Убираем прямой доступ к таблицам с отдельными записями.
REVOKE ALL PRIVILEGES ON
    public.applications,
    public.grades,
    public.courses,
    public.teachers,
    public.departments
FROM api_reader;

GRANT SELECT ON public.admissions_summary TO api_reader;
GRANT SELECT ON public.grade_summary TO api_reader;
GRANT SELECT ON public.programs TO api_reader;

ALTER ROLE api_reader SET default_transaction_read_only = on;
ALTER ROLE api_reader SET statement_timeout = '3s';