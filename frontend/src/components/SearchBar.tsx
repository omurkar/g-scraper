'use client'

import { useState } from 'react'
import { Search, MapPin, Zap, Loader2 } from 'lucide-react'

interface Props {
  onSearch: (keyword: string, location: string) => void
  loading?: boolean
}

export default function SearchBar({ onSearch, loading }: Props) {
  const [keyword, setKeyword] = useState('')
  const [location, setLocation] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (keyword.trim() && location.trim()) {
      onSearch(keyword.trim(), location.trim())
    }
  }

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <div className="card animate-pulse-glow p-6" style={{ borderRadius: 16 }}>
        <div className="flex items-center gap-3 mb-5">
          <div style={{
            background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
            borderRadius: 10,
            padding: 8,
            display: 'flex',
          }}>
            <Zap size={20} color="white" />
          </div>
          <div>
            <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
              Find Leads Instantly
            </h2>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', margin: 0 }}>
              Search Google Maps → Extract contacts → AI verify
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          {/* Keyword */}
          <div style={{ flex: '1 1 240px', position: 'relative' }}>
            <Search
              size={16}
              style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }}
            />
            <input
              id="search-keyword"
              className="input-field"
              style={{ width: '100%', paddingLeft: 38 }}
              type="text"
              placeholder="e.g. Dentists, Restaurants, Law firms"
              value={keyword}
              onChange={e => setKeyword(e.target.value)}
              disabled={loading}
              required
            />
          </div>

          {/* Location */}
          <div style={{ flex: '1 1 200px', position: 'relative' }}>
            <MapPin
              size={16}
              style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }}
            />
            <input
              id="search-location"
              className="input-field"
              style={{ width: '100%', paddingLeft: 38 }}
              type="text"
              placeholder="e.g. Mumbai, New York, London"
              value={location}
              onChange={e => setLocation(e.target.value)}
              disabled={loading}
              required
            />
          </div>

          {/* Submit */}
          <button
            id="search-submit"
            type="submit"
            className="btn-primary"
            style={{ flex: '0 0 auto', minWidth: 140, display: 'flex', alignItems: 'center', gap: 8 }}
            disabled={loading || !keyword.trim() || !location.trim()}
          >
            {loading ? (
              <>
                <Loader2 size={16} className="animate-spin-slow" />
                Searching…
              </>
            ) : (
              <>
                <Zap size={16} />
                Find Leads
              </>
            )}
          </button>
        </div>

        {/* Example queries */}
        <div style={{ marginTop: 14, display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Try:</span>
          {[
            ['Dentists', 'Mumbai'],
            ['Coffee Shops', 'London'],
            ['Law Firms', 'New York'],
          ].map(([kw, loc]) => (
            <button
              key={kw}
              type="button"
              onClick={() => { setKeyword(kw); setLocation(loc) }}
              style={{
                background: 'rgba(99,102,241,0.1)',
                border: '1px solid rgba(99,102,241,0.2)',
                borderRadius: 6,
                padding: '3px 10px',
                fontSize: '0.75rem',
                color: 'var(--accent)',
                cursor: 'pointer',
                transition: 'background 0.15s',
              }}
              onMouseEnter={e => (e.currentTarget.style.background = 'rgba(99,102,241,0.2)')}
              onMouseLeave={e => (e.currentTarget.style.background = 'rgba(99,102,241,0.1)')}
            >
              {kw} in {loc}
            </button>
          ))}
        </div>
      </div>
    </form>
  )
}
