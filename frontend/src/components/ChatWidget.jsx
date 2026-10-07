import MessageList from './MessageList'
import InputArea from './InputArea'
import LoadingIndicator from './LoadingIndicator'
import ErrorBlock from './ErrorBlock'
import useChat from '../hooks/useChat'

export default function ChatWidget({ onClose }) {
  const { messages, isLoading, error, sendMessage } = useChat()

  return (
    <div className="w-[400px] h-[600px] bg-white rounded-2xl shadow-2xl overflow-hidden flex flex-col border border-gray-200">
      {/* Шапка с кнопкой закрытия */}
      <div className="p-4 bg-blue-600 text-white flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold">Чат-ассистент</h1>
          <p className="text-xs text-blue-100">Задайте вопрос о данных университета</p>
        </div>
        <button
          onClick={onClose}
          className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-blue-700 transition-colors text-xl"
          title="Закрыть чат"
        >
          ✕
        </button>
      </div>

      {/* Блок ошибки */}
      <ErrorBlock error={error} />

      {/* История сообщений */}
      <MessageList messages={messages} />

      {/* Индикатор загрузки */}
      {isLoading && (
        <div className="px-4 pb-2">
          <LoadingIndicator />
        </div>
      )}

      {/* Поле ввода */}
      <InputArea onSend={sendMessage} isLoading={isLoading} />
    </div>
  )
}