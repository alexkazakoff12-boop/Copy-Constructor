// Vite перенаправляет /api/chat на FastAPI /chat при локальной разработке.
const API_URL = '/api/chat'

export async function sendQuestion(question) {
  let response
  try {
    response = await fetch(API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
    })
  } catch {
    throw new Error('Нет соединения с сервером. Проверьте, что FastAPI запущен.')
  }

  if (!response.ok) {
    if (response.status === 502) {
      throw new Error('FastAPI недоступен. Запустите backend на порту 8000.')
    }
    throw new Error(`Ошибка сервера: ${response.status}`)
  }

  const result = await response.json()
  if (result.error) throw new Error(result.error)

  // Текущий backend присылает названия столбцов и строки отдельно;
  // компонент DataTable ожидает массив объектов.
  const data = result.rows?.map((row) =>
    Object.fromEntries(result.columns.map((column, index) => [column, row[index]])),
  ) ?? []

  return { ...result, data }
}
