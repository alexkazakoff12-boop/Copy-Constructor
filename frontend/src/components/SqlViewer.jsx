export default function SqlViewer({ sql }) {
  if (!sql) return null

  return (
    <div className="mt-2 p-3 bg-gray-900 rounded-lg">
      <p className="text-xs text-gray-400 mb-1">SQL-запрос:</p>
      <code className="text-green-400 text-sm font-mono block whitespace-pre-wrap">
        {sql}
      </code>
    </div>
  )
}