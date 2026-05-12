import { useMemo } from 'react'
import { useAppState } from '../store/useAppState'

export default function DashboardPage() {
  const { state } = useAppState()
  const stats = useMemo(() => {
    const totalConversations = state.conversations.length
    const totalMessages = state.conversations.reduce((a, c) => a + c.messages.length, 0)
    const assistantMessages = state.conversations.reduce((a, c) => a + c.messages.filter(m => m.role === 'assistant').length, 0)
    return { totalConversations, totalMessages, assistantMessages }
  }, [state])

  return <div className="space-y-4">
    <h2 className="text-2xl font-bold">Conversation Intelligence Dashboard</h2>
    <div className="grid grid-cols-3 gap-4">{Object.entries(stats).map(([k,v]) => <div key={k} className="rounded-xl border border-slate-800 bg-slate-900 p-4"><div className="text-slate-400 text-sm">{k}</div><div className="text-3xl font-bold">{v}</div></div>)}</div>
    <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
      <h3 className="mb-2 font-semibold">Top Conversations</h3>
      <div className="space-y-2">{state.conversations.map(c => <div key={c.id} className="rounded bg-slate-800 p-2 flex justify-between"><span>{c.title}</span><span className="text-slate-400 text-sm">{c.messages.length} msgs</span></div>)}</div>
    </div>
  </div>
}
