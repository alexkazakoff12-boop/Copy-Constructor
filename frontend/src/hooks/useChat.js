import { useState } from 'react'
import { sendQuestion } from '../api/chatApi'

export default function useChat() {
  const [messages, setMessages] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  const sendMessage = async (question) => {
    const userMessage = { role: 'user', content: question }
    setMessages((prev) => [...prev, userMessage])
    setIsLoading(true)
    setError(null)

    try {
      const response = await sendQuestion(question)

      const botMessage = {
        role: 'assistant',
        content: response.answer || 'Ответ получен',
        sql: response.sql || null,
        data: response.data || null,
      }
      setMessages((prev) => [...prev, botMessage])
    } catch (err) {
      setError(err.message)
    } finally {
      setIsLoading(false)
    }
  }

  return { messages, isLoading, error, sendMessage }
}