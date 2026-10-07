import MessageBubble from './MessageBubble'
import SqlViewer from './SqlViewer'
import DataTable from './DataTable'

export default function MessageList({ messages }) {
  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {messages.map((msg, idx) => (
        <div key={idx}>
          <MessageBubble message={msg} />
          {msg.role === 'assistant' && (
            <>
              <SqlViewer sql={msg.sql} />
              <DataTable data={msg.data} />
            </>
          )}
        </div>
      ))}
    </div>
  )
}