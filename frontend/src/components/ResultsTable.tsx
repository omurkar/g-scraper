'use client'

import { useState, useMemo } from 'react'
import { type Lead } from '@/lib/types'
import {
  Globe, Phone, MapPin, Star, Mail,
  ChevronUp, ChevronDown, Search,
  ExternalLink, Flame, Thermometer, Snowflake
} from 'lucide-react'

interface Props {
  leads: Lead[]
  loading?: boolean
}

type SortKey = 'business_name' | 'rating' | 'status' | 'quality_score'
type SortDir = 'asc' | 'desc'
type QualityFilter = 'all' | 'hot' | 'warm' | 'cold'

const QUALITY_ICONS = {
  hot:  <Flame size={12} />,
  warm: <Thermometer size={12} />,
  cold: <Snowflake size={12} />,
}

function QualityBadge({ score }: { score?: string | null }) {
  if (!score) return <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>—</span>
  return (
    <span className={`badge badge-${score}`} style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
      {QUALITY_ICONS[score as keyof typeof QUALITY_ICONS]}
      {score.toUpperCase()}
    </span>
  )
}

function StatusDot({ status }: { status: string }) {
  const colors: Record<string, string> = {
    scraped: '#64748b',
    enriching: '#f59e0b',
    enriched: '#6366f1',
    verified: '#10b981',
  }
  return (
    <span style={{
      display: 'inline-block',
      width: 7, height: 7,
      borderRadius: '50%',
      background: colors[status] || '#64748b',
      marginRight: 5,
    }} />
  )
}

export default function ResultsTable({ leads, loading }: Props) {
  const [search, setSearch] = useState('')
  const [sortKey, setSortKey] = useState<SortKey>('business_name')
  const [sortDir, setSortDir] = useState<SortDir>('asc')
  const [qualityFilter, setQualityFilter] = useState<QualityFilter>('all')
  const [expandedId, setExpandedId] = useState<string | null>(null)

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    else { setSortKey(key); setSortDir('asc') }
  }

  const filtered = useMemo(() => {
    let data = [...leads]
    if (search) {
      const q = search.toLowerCase()
      data = data.filter(l =>
        l.business_name.toLowerCase().includes(q) ||
        l.address?.toLowerCase().includes(q) ||
        l.category?.toLowerCase().includes(q) ||
        l.enrichment?.emails?.some(e => e.includes(q))
      )
    }
    if (qualityFilter !== 'all') {
      data = data.filter(l => l.verification?.quality_score === qualityFilter)
    }
    data.sort((a, b) => {
      let va: string | number = ''
      let vb: string | number = ''
      if (sortKey === 'business_name') { va = a.business_name; vb = b.business_name }
      else if (sortKey === 'rating') { va = a.rating ?? -1; vb = b.rating ?? -1 }
      else if (sortKey === 'status') { va = a.status; vb = b.status }
      else if (sortKey === 'quality_score') { va = a.verification?.quality_score ?? 'zzz'; vb = b.verification?.quality_score ?? 'zzz' }
      if (va < vb) return sortDir === 'asc' ? -1 : 1
      if (va > vb) return sortDir === 'asc' ? 1 : -1
      return 0
    })
    return data
  }, [leads, search, sortKey, sortDir, qualityFilter])

  const SortIcon = ({ k }: { k: SortKey }) => {
    if (sortKey !== k) return <span style={{ color: 'var(--text-muted)', opacity: 0.4 }}><ChevronUp size={12} /></span>
    return sortDir === 'asc' ? <ChevronUp size={12} style={{ color: 'var(--accent)' }} /> : <ChevronDown size={12} style={{ color: 'var(--accent)' }} />
  }

  if (loading && leads.length === 0) {
    return (
      <div style={{ padding: 32, textAlign: 'center' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12, alignItems: 'center' }}>
          {[1,2,3,4,5].map(i => (
            <div key={i} className="skeleton" style={{ width: '100%', height: 48 }} />
          ))}
        </div>
      </div>
    )
  }

  if (!leads.length) {
    return (
      <div style={{ padding: 48, textAlign: 'center' }}>
        <div style={{ fontSize: '2.5rem', marginBottom: 12 }}>🔍</div>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
          No leads yet — run a search above to start discovering businesses.
        </p>
      </div>
    )
  }

  return (
    <div>
      {/* Controls */}
      <div style={{ padding: '14px 20px', display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap', borderBottom: '1px solid var(--border)' }}>
        <div style={{ position: 'relative', flex: '1 1 220px' }}>
          <Search size={14} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
          <input
            className="input-field"
            style={{ paddingLeft: 32, paddingTop: 7, paddingBottom: 7, width: '100%' }}
            placeholder="Filter leads…"
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>

        <div style={{ display: 'flex', gap: 6 }}>
          {(['all', 'hot', 'warm', 'cold'] as QualityFilter[]).map(q => (
            <button
              key={q}
              onClick={() => setQualityFilter(q)}
              style={{
                padding: '5px 12px',
                borderRadius: 8,
                border: '1px solid',
                fontSize: '0.78rem',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.15s',
                background: qualityFilter === q
                  ? q === 'all' ? 'rgba(99,102,241,0.2)' : q === 'hot' ? 'rgba(239,68,68,0.2)' : q === 'warm' ? 'rgba(245,158,11,0.2)' : 'rgba(59,130,246,0.2)'
                  : 'transparent',
                borderColor: qualityFilter === q
                  ? q === 'all' ? 'var(--accent)' : q === 'hot' ? 'var(--hot)' : q === 'warm' ? 'var(--warm)' : 'var(--cold)'
                  : 'var(--border)',
                color: qualityFilter === q
                  ? q === 'all' ? 'var(--accent)' : q === 'hot' ? 'var(--hot)' : q === 'warm' ? 'var(--warm)' : 'var(--cold)'
                  : 'var(--text-muted)',
              }}
            >
              {q === 'all' ? 'All' : q.charAt(0).toUpperCase() + q.slice(1)}
            </button>
          ))}
        </div>

        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginLeft: 'auto' }}>
          {filtered.length} / {leads.length} leads
        </span>
      </div>

      {/* Table */}
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.83rem' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border)' }}>
              {[
                { label: 'Business', key: 'business_name' as SortKey },
                { label: 'Rating', key: 'rating' as SortKey },
                { label: 'Contact' },
                { label: 'Emails' },
                { label: 'Socials' },
                { label: 'Quality', key: 'quality_score' as SortKey },
                { label: 'Status', key: 'status' as SortKey },
                { label: '' },
              ].map(({ label, key }) => (
                <th
                  key={label}
                  onClick={key ? () => toggleSort(key) : undefined}
                  style={{
                    padding: '10px 16px',
                    textAlign: 'left',
                    color: 'var(--text-muted)',
                    fontWeight: 600,
                    fontSize: '0.76rem',
                    letterSpacing: '0.05em',
                    textTransform: 'uppercase',
                    cursor: key ? 'pointer' : 'default',
                    userSelect: 'none',
                    whiteSpace: 'nowrap',
                  }}
                >
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                    {label}
                    {key && <SortIcon k={key} />}
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map((lead, idx) => {
              const expanded = expandedId === lead.id
              return [
                <tr
                  key={lead.id}
                  className="card-hover"
                  onClick={() => setExpandedId(expanded ? null : lead.id)}
                  style={{
                    borderBottom: '1px solid rgba(99,102,241,0.06)',
                    cursor: 'pointer',
                    background: idx % 2 === 0 ? 'transparent' : 'rgba(99,102,241,0.02)',
                    transition: 'background 0.15s',
                    animationDelay: `${idx * 30}ms`,
                  }}
                  className={`animate-slide-in card-hover`}
                >
                  {/* Business name */}
                  <td style={{ padding: '12px 16px', maxWidth: 220 }}>
                    <div style={{ fontWeight: 600, color: 'var(--text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {lead.business_name}
                    </div>
                    {lead.category && (
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: 2 }}>{lead.category}</div>
                    )}
                  </td>

                  {/* Rating */}
                  <td style={{ padding: '12px 16px', whiteSpace: 'nowrap' }}>
                    {lead.rating ? (
                      <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                        <Star size={12} style={{ color: '#f59e0b', fill: '#f59e0b' }} />
                        <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{lead.rating}</span>
                        {lead.review_count && <span style={{ color: 'var(--text-muted)', fontSize: '0.72rem' }}>({lead.review_count})</span>}
                      </span>
                    ) : <span style={{ color: 'var(--text-muted)' }}>—</span>}
                  </td>

                  {/* Contact */}
                  <td style={{ padding: '12px 16px', maxWidth: 180 }}>
                    {lead.phone && (
                      <div style={{ display: 'flex', alignItems: 'center', gap: 4, color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                        <Phone size={11} /> {lead.phone}
                      </div>
                    )}
                    {lead.address && (
                      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 4, color: 'var(--text-muted)', fontSize: '0.75rem', marginTop: 2 }}>
                        <MapPin size={11} style={{ flexShrink: 0, marginTop: 1 }} />
                        <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 160 }}>{lead.address}</span>
                      </div>
                    )}
                  </td>

                  {/* Emails */}
                  <td style={{ padding: '12px 16px', maxWidth: 200 }}>
                    {lead.enrichment?.emails?.length ? (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                        {lead.enrichment.emails.slice(0, 2).map(e => (
                          <a key={e} href={`mailto:${e}`} onClick={ev => ev.stopPropagation()}
                            style={{ color: 'var(--accent)', fontSize: '0.78rem', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 4 }}
                            onMouseEnter={ev => (ev.currentTarget.style.textDecoration = 'underline')}
                            onMouseLeave={ev => (ev.currentTarget.style.textDecoration = 'none')}
                          >
                            <Mail size={11} /> {e}
                          </a>
                        ))}
                        {(lead.enrichment.emails.length > 2) && (
                          <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>+{lead.enrichment.emails.length - 2} more</span>
                        )}
                      </div>
                    ) : <span style={{ color: 'var(--text-muted)', fontSize: '0.78rem' }}>
                      {lead.status === 'scraped' ? 'Pending…' : 'Not found'}
                    </span>}
                  </td>

                  {/* Socials */}
                  <td style={{ padding: '12px 16px' }}>
                    <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap' }}>
                      {lead.enrichment?.linkedin_url && (
                        <a href={lead.enrichment.linkedin_url} target="_blank" rel="noreferrer" onClick={e => e.stopPropagation()}
                          style={{ fontSize: '0.68rem', fontWeight: 700, padding: '2px 6px', borderRadius: 4, background: 'rgba(10,102,194,0.15)', color: '#0a66c2', textDecoration: 'none' }}>in</a>
                      )}
                      {lead.enrichment?.instagram_url && (
                        <a href={lead.enrichment.instagram_url} target="_blank" rel="noreferrer" onClick={e => e.stopPropagation()}
                          style={{ fontSize: '0.68rem', fontWeight: 700, padding: '2px 6px', borderRadius: 4, background: 'rgba(225,48,108,0.15)', color: '#e1306c', textDecoration: 'none' }}>ig</a>
                      )}
                      {lead.enrichment?.facebook_url && (
                        <a href={lead.enrichment.facebook_url} target="_blank" rel="noreferrer" onClick={e => e.stopPropagation()}
                          style={{ fontSize: '0.68rem', fontWeight: 700, padding: '2px 6px', borderRadius: 4, background: 'rgba(24,119,242,0.15)', color: '#1877f2', textDecoration: 'none' }}>fb</a>
                      )}
                      {lead.enrichment?.twitter_url && (
                        <a href={lead.enrichment.twitter_url} target="_blank" rel="noreferrer" onClick={e => e.stopPropagation()}
                          style={{ fontSize: '0.68rem', fontWeight: 700, padding: '2px 6px', borderRadius: 4, background: 'rgba(29,161,242,0.15)', color: '#1da1f2', textDecoration: 'none' }}>𝕏</a>
                      )}
                      {!lead.enrichment && <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>—</span>}
                    </div>
                  </td>

                  {/* Quality */}
                  <td style={{ padding: '12px 16px' }}>
                    <QualityBadge score={lead.verification?.quality_score} />
                  </td>

                  {/* Status */}
                  <td style={{ padding: '12px 16px', whiteSpace: 'nowrap' }}>
                    <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                      <StatusDot status={lead.status} />
                      {lead.status}
                    </span>
                  </td>

                  {/* Links */}
                  <td style={{ padding: '12px 16px' }}>
                    <div style={{ display: 'flex', gap: 6 }}>
                      {lead.website_url && (
                        <a href={lead.website_url} target="_blank" rel="noreferrer" onClick={e => e.stopPropagation()}
                          title="Visit website"
                          style={{ color: 'var(--text-muted)', transition: 'color 0.15s' }}
                          onMouseEnter={e => (e.currentTarget.style.color = 'var(--accent)')}
                          onMouseLeave={e => (e.currentTarget.style.color = 'var(--text-muted)')}
                        >
                          <Globe size={14} />
                        </a>
                      )}
                      {lead.google_maps_url && (
                        <a href={lead.google_maps_url} target="_blank" rel="noreferrer" onClick={e => e.stopPropagation()}
                          title="Open in Google Maps"
                          style={{ color: 'var(--text-muted)', transition: 'color 0.15s' }}
                          onMouseEnter={e => (e.currentTarget.style.color = '#10b981')}
                          onMouseLeave={e => (e.currentTarget.style.color = 'var(--text-muted)')}
                        >
                          <MapPin size={14} />
                        </a>
                      )}
                    </div>
                  </td>
                </tr>,

                /* Expanded row — AI reasoning */
                expanded && lead.verification?.ai_reasoning ? (
                  <tr key={`${lead.id}-expanded`} style={{ background: 'rgba(99,102,241,0.05)' }}>
                    <td colSpan={8} style={{ padding: '10px 20px 14px' }}>
                      <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
                        <div style={{
                          background: 'rgba(99,102,241,0.15)',
                          borderRadius: 6,
                          padding: '2px 8px',
                          fontSize: '0.72rem',
                          fontWeight: 700,
                          color: 'var(--accent)',
                          whiteSpace: 'nowrap',
                        }}>
                          🤖 AI Reasoning
                        </div>
                        <p style={{ margin: 0, fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                          {lead.verification.ai_reasoning}
                        </p>
                      </div>
                    </td>
                  </tr>
                ) : null
              ]
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
