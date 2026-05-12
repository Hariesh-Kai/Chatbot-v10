import { useState } from 'react'
import { useAppState } from '../store/useAppState'

export default function SettingsPage() {
  const { state, setState } = useAppState()
  const [apiKey, setApiKey] = useState(state.openrouter.apiKey)
  const [model, setModel] = useState(state.openrouter.model)

  function save() {
    setState(s => ({ ...s, openrouter: { apiKey, model } }))
    alert('Settings saved')
  }

  return <div className="max-w-2xl rounded-xl border border-slate-800 bg-slate-900 p-4 space-y-3">
    <h2 className="text-2xl font-bold">Model Settings</h2>
    <p className="text-slate-400 text-sm">Configure OpenRouter API key and model for optional answer refinement.</p>
    <input className="w-full rounded bg-slate-800 p-3" placeholder="OpenRouter API Key" value={apiKey} onChange={e=>setApiKey(e.target.value)} />
    <input className="w-full rounded bg-slate-800 p-3" placeholder="Model e.g. openai/gpt-4o-mini" value={model} onChange={e=>setModel(e.target.value)} />
    <button onClick={save} className="rounded bg-emerald-500 px-4 py-2 font-semibold text-slate-900">Save</button>
  </div>
}
