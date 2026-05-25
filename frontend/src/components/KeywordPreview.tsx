'use client'

import { useEffect, useState, useRef } from 'react'
import { Zap, Eye } from 'lucide-react'

interface Props {
  categories: string[]
  city: string
  localities: string[]
  selectAllLocalities: boolean
  onChange: (kws: string[]) => void
}

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function KeywordPreview({ categories, city, localities, selectAllLocalities, onChange }: Props) {
  const [keywords, setKeywords] = useState<string[]>([])
  const [loading, setLoading] = useState(false)

  // Hold onChange in a ref so it's never a useEffect dependency
  const onChangeRef = useRef(onChange)
  useEffect(() => { onChangeRef.current = onChange })

  // Serialize arrays so effect only re-runs when values actually change
  const categoriesKey = JSON.stringify(categories)
  const localitiesKey = JSON.stringify(localities)

  useEffect(() => {
    if (!city || categories.length === 0) {
      setKeywords([])
      onChangeRef.current([])
      return
    }
    const timer = setTimeout(async () => {
      setLoading(true)
      try {
        const body = {
          keyword: categories[0],
          location: city,
          categories,
          localities,
          select_all_localities: selectAllLocalities,
          lead_goal: 30,
        }
        const r = await fetch(`${API}/api/keyword-preview`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        })
        const data = await r.json()
        setKeywords(data.keywords || [])
        onChangeRef.current(data.keywords || [])
      } catch {
        setKeywords([])
      } finally {
        setLoading(false)
      }
    }, 400)
    return () => clearTimeout(timer)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [categoriesKey, city, localitiesKey, selectAllLocalities])

  if (keywords.length === 0) return null

  return (
    <div className="card" style={{ borderRadius: 12, overflow: 'hidden' }}>
      <div style={{ padding: '10px 16px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: 8 }}>
        <Eye size={14} style={{ color: 'var(--accent)' }} />
        <span style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
          Keyword Preview
        </span>
        <span style={{
          marginLeft: 'auto', background: 'rgba(99,102,241,0.15)', color: 'var(--accent)',
          border: '1px solid rgba(99,102,241,0.3)', borderRadius: 20, padding: '1px 8px',
          fontSize: '0.72rem', fontWeight: 700,
        }}>
          {loading ? '…' : `${keywords.length} queries`}
        </span>
      </div>

      <div style={{ padding: '10px 14px', maxHeight: 200, overflowY: 'auto' }}>
        {keywords.slice(0, 30).map((kw, i) => (
          <div key={i} style={{
            display: 'flex', alignItems: 'center', gap: 8,
            padding: '4px 0',
            borderBottom: i < keywords.slice(0, 30).length - 1 ? '1px solid rgba(99,102,241,0.06)' : 'none',
          }}>
            <Zap size={10} style={{ color: 'var(--accent)', flexShrink: 0 }} />
            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{kw}</span>
          </div>
        ))}
        {keywords.length > 30 && (
          <div style={{ padding: '6px 0', fontSize: '0.75rem', color: 'var(--text-muted)', textAlign: 'center' }}>
            + {keywords.length - 30} more queries…
          </div>
        )}
      </div>
    </div>
  )
}
