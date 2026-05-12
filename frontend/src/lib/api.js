export async function uploadDocument(file, documentId) {
  const form = new FormData()
  form.append('document_id', documentId)
  form.append('file', file)
  const res = await fetch('/v1/documents/upload', { method: 'POST', body: form })
  if (!res.ok) throw new Error('Upload failed')
  return res.json()
}

export async function askRag(question, document_id) {
  const res = await fetch('/v1/query', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, document_id, top_k: 5 })
  })
  if (!res.ok) throw new Error('Query failed')
  return res.json()
}

export async function askOpenRouter(question, apiKey, model) {
  const res = await fetch('https://openrouter.ai/api/v1/chat/completions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${apiKey}` },
    body: JSON.stringify({ model, messages: [{ role: 'user', content: question }] })
  })
  if (!res.ok) throw new Error('OpenRouter request failed')
  const data = await res.json()
  return data.choices?.[0]?.message?.content || 'No response'
}
