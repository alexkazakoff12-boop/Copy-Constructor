import { useState } from 'react'
import ChatWidget from './components/ChatWidget'

function App() {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Синяя шапка университета */}
      <header className="bg-blue-700 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center gap-4">
          <img
            src="/logo2.png"
            alt="Эмблема РГУНГ"
            className="w-16 h-16 object-contain"
          />
          <div>
            <h1 className="text-2xl font-bold tracking-wide">
              Российский государственный университет нефти и газа
            </h1>
            <p className="text-blue-100 text-sm">
              имени И.М. Губкина
            </p>
          </div>
        </div>
      </header>

      {/* Основной контент страницы */}
      <main className="max-w-7xl mx-auto px-6 py-12">
        <h2 className="text-3xl font-bold text-gray-800 mb-4">
          Добро пожаловать
        </h2>
        <p className="text-gray-600 mb-8 text-lg">
          Чат-ассистент поможет вам получить информацию о данных университета.
          Нажмите на кнопку в правом нижнем углу, чтобы начать диалог.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white p-6 rounded-lg shadow-md border border-gray-100">
            <h3 className="font-bold text-lg mb-2 text-gray-800">Факультеты</h3>
            <p className="text-gray-500">10 факультетов</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-md border border-gray-100">
            <h3 className="font-bold text-lg mb-2 text-gray-800">Студенты</h3>
            <p className="text-gray-500">10 000+ учащихся</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-md border border-gray-100">
            <h3 className="font-bold text-lg mb-2 text-gray-800">Преподаватели</h3>
            <p className="text-gray-500">800+ сотрудников</p>
          </div>
        </div>
      </main>

      {/* Плавающая кнопка открытия чата */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 w-16 h-16 bg-blue-600 hover:bg-blue-700 text-white rounded-full shadow-2xl flex items-center justify-center text-3xl transition-all hover:scale-110 z-50"
          title="Открыть чат-ассистент"
        >
          💬
        </button>
      )}

      {/* Виджет чата */}
      {isOpen && (
        <div className="fixed bottom-6 right-6 z-50 animate-slide-up">
          <ChatWidget onClose={() => setIsOpen(false)} />
        </div>
      )}
    </div>
  )
}

export default App