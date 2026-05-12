import { useMemo, useState } from 'react'
import { askOpenRouter, askRag, uploadDocument } from '../lib/api'
import { useAppState } from '../store/useAppState'

export default function ChatPage() {
  const { state, setState } = useAppState()
  const [question, setQuestion] = useState('')
  const [documentId, setDocumentId] = useState('doc-1')
  const [busy, setBusy] = useState(false)

  const active = useMemo(() => state.conversations.find(c => c.id === state.activeId), [state])

  function ensureConversation() {
    if (active) return active
    const conv = { id: crypto.randomUUID(), title: 'New Conversation', messages: [], createdAt: new Date().toISOString() }
    setState(s => ({ ...s, activeId: conv.id, conversations: [conv, ...s.conversations] }))
    return conv
  }

  async function send() {
    if (!question.trim()) return
    const q = question
    setQuestion('')
    setBusy(true)
    const conv = ensureConversation()
    const userMsg = { role: 'user', content: q, ts: Date.now() }

    setState(s => ({ ...s, conversations: s.conversations.map(c => c.id === conv.id ? { ...c, title: c.title === 'New Conversation' ? q.slice(0, 50) : c.title, messages: [...c.messages, userMsg] } : c) }))

    try {
      const rag = await askRag(q, documentId)
      let content = `${rag.answer}\n\nConfidence: ${Number(rag.confidence || 0).toFixed(2)}`
      if (state.openrouter.apiKey) {
        const llm = await askOpenRouter(`Refine this grounded answer without changing facts:\n${rag.answer}`, state.openrouter.apiKey, state.openrouter.model)
        content += `\n\nOpenRouter refinement:\n${llm}`
      }
      const cites = (rag.citations || []).map(c => `${c.document_id}:${c.chunk_id} p.${c.page_start ?? '-'} ${c.section ?? ''}`).join(' | ')
      const botMsg = { role: 'assistant', content, cites, ts: Date.now() }
      setState(s => ({ ...s, conversations: s.conversations.map(c => c.id === conv.id ? { ...c, messages: [...c.messages, botMsg] } : c) }))
    } catch (e) {
      const botMsg = { role: 'assistant', content: 'Request failed. Verify backend and settings.', ts: Date.now() }
      setState(s => ({ ...s, conversations: s.conversations.map(c => c.id === conv.id ? { ...c, messages: [...c.messages, botMsg] } : c) }))
    } finally { setBusy(false) }
  }

  return <div className="grid grid-cols-12 gap-4">
    <aside className="col-span-3 rounded-xl border border-slate-800 bg-slate-900 p-3">
      <button className="mb-3 w-full rounded bg-blue-600 px-3 py-2" onClick={() => setState(s => ({ ...s, activeId: null }))}>+ New Chat</button>
      <div className="space-y-2 max-h-[70vh] overflow-auto">{state.conversations.map(c => <button key={c.id} onClick={() => setState(s => ({ ...s, activeId: c.id }))} className="w-full rounded bg-slate-800 p-2 text-left text-sm">{c.title}</button>)}</div>
    </aside>
    <section className="col-span-9 rounded-xl border border-slate-800 bg-slate-900 p-3">
      <div className="mb-3 flex gap-2"><input className="rounded bg-slate-800 p-2" placeholder="document_id" value={documentId} onChange={e => setDocumentId(e.target.value)} /><label className="rounded bg-slate-800 p-2 text-sm cursor-pointer">Upload <input type="file" className="hidden" onChange={async (e) => { const file = e.target.files?.[0]; if (!file) return; try { const out = await uploadDocument(file, documentId); alert(`Uploaded. Indexed ${out.chunks_indexed} chunks.`) } catch (err) { alert(`Upload failed: ${err.message}`) } }} /></label></div>
      <div className="h-[56vh] overflow-auto space-y-2 rounded border border-slate-800 p-3">{(active?.messages || []).map((m, i) => <div key={i} className={`rounded p-2 ${m.role==='user'?'bg-blue-600/40 ml-16':'bg-slate-800 mr-16'}`}><div>{m.content}</div>{m.cites && <div className="mt-2 text-xs text-slate-400">{m.cites}</div>}</div>)}</div>
      <div className="mt-3 flex gap-2"><input className="flex-1 rounded bg-slate-800 p-3" placeholder="Ask engineering question..." value={question} onChange={e => setQuestion(e.target.value)} onKeyDown={e=> e.key==='Enter' && send()} /><button disabled={busy} onClick={send} className="rounded bg-cyan-500 px-4 py-2 font-semibold text-slate-900">{busy?'Thinking...':'Send'}</button></div>
    </section>
  </div>
}
