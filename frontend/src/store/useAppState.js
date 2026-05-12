import { useEffect, useState } from 'react'

const KEY = 'industrial-rag-state'

export function useAppState() {
  const [state, setState] = useState(() => {
    const raw = localStorage.getItem(KEY)
    return raw ? JSON.parse(raw) : { conversations: [], activeId: null, openrouter: { apiKey: '', model: 'openai/gpt-4o-mini' } }
  })

  useEffect(() => localStorage.setItem(KEY, JSON.stringify(state)), [state])

  return { state, setState }
}
