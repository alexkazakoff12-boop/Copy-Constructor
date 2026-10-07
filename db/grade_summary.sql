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

GRANT SELECT ON public.grade_summary TO api_reader;CREATE OR REPLACE VIEW public.grade_summary AS
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

GRANT SELECT ON public.grade_summary TO api_reader;