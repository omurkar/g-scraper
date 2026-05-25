'use client'

import { useState, useEffect, useMemo } from 'react'
import { ChevronDown, Check, Search, Plus, X } from 'lucide-react'

interface Props {
  selectedCategories: string[]
  onChange: (cats: string[]) => void
  disabled?: boolean
}

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function CategoryPicker({ selectedCategories, onChange, disabled }: Props) {
  const [categories, setCategories] = useState<string[]>([])
  const [open, setOpen] = useState(false)
  const [filter, setFilter] = useState('')

  useEffect(() => {
    fetch(`${API}/api/categories`).then(r => r.json()).then(setCategories).catch(() => {})
  }, [])

  const filtered = useMemo(() =>
    categories.filter(c => c.toLowerCase().includes(filter.toLowerCase())),
    [categories, filter]
  )

  const toggle = (cat: string) => {
    if (selectedCategories.includes(cat)) onChange(selectedCategories.filter(c => c !== cat))
    else onChange([...selectedCategories, cat])
  }

  const removeChip = (cat: string) => onChange(selectedCategories.filter(c => c !== cat))

  return (
    <div style={{ position: 'relative' }}>
      <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
        Categories
      </label>

      {/* Chip display */}
      {selectedCategories.length > 0 && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 8 }}>
          {selectedCategories.map(cat => (
            <span key={cat} style={{
              display: 'inline-flex', alignItems: 'center', gap: 4,
              background: 'rgba(99,102,241,0.15)', color: 'var(--accent)',
              border: '1px solid rgba(99,102,241,0.3)',
              borderRadius: 20, padding: '3px 10px', fontSize: '0.75rem', fontWeight: 600,
            }}>
              {cat}
              <button onClick={() => removeChip(cat)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--accent)', display: 'flex', padding: 0 }}>
                <X size={12} />
              </button>
            </span>
          ))}
        </div>
      )}

      {/* Dropdown trigger */}
      <button
        type="button"
        onClick={() => setOpen(o => !o)}
        disabled={disabled}
        className="input-field"
        style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer' }}
      >
        <span style={{ color: selectedCategories.length ? 'var(--text-primary)' : 'var(--text-muted)' }}>
          {selectedCategories.length ? `${selectedCategories.length} selected` : 'Select categories…'}
        </span>
        <ChevronDown size={15} style={{ color: 'var(--text-muted)', transform: open ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }} />
      </button>

      {open && (
        <div style={{
          position: 'absolute', top: '100%', left: 0, right: 0, zIndex: 100,
          background: 'var(--bg-panel)', border: '1px solid var(--border)',
          borderRadius: 10, boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
          marginTop: 4, overflow: 'hidden',
        }}>
          {/* Filter input */}
          <div style={{ padding: '10px 12px', borderBottom: '1px solid var(--border)', position: 'relative' }}>
            <Search size={13} style={{ position: 'absolute', left: 22, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
            <input
              className="input-field"
              style={{ width: '100%', paddingLeft: 32, paddingTop: 6, paddingBottom: 6, fontSize: '0.82rem' }}
              placeholder="Search categories…"
              value={filter}
              onChange={e => setFilter(e.target.value)}
              autoFocus
            />
          </div>
          <div style={{ maxHeight: 240, overflowY: 'auto' }}>
            {filtered.map(cat => {
              const selected = selectedCategories.includes(cat)
              return (
                <div
                  key={cat}
                  onClick={() => toggle(cat)}
                  style={{
                    padding: '9px 14px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 10,
                    background: selected ? 'rgba(99,102,241,0.08)' : 'transparent',
                    fontSize: '0.85rem', color: selected ? 'var(--accent)' : 'var(--text-primary)',
                    transition: 'background 0.1s',
                  }}
                  onMouseEnter={e => !selected && (e.currentTarget.style.background = 'rgba(99,102,241,0.05)')}
                  onMouseLeave={e => !selected && (e.currentTarget.style.background = 'transparent')}
                >
                  <div style={{
                    width: 16, height: 16, borderRadius: 4, border: `1.5px solid ${selected ? 'var(--accent)' : 'var(--border)'}`,
                    background: selected ? 'var(--accent)' : 'transparent',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
                  }}>
                    {selected && <Check size={10} color="white" />}
                  </div>
                  {cat}
                </div>
              )
            })}
          </div>
          <div style={{ padding: '8px 12px', borderTop: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{selectedCategories.length} selected</span>
            <button onClick={() => { onChange([]); setOpen(false); }}
              style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '0.75rem' }}>
              Clear all
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
