'use client'

import { type SearchJob } from '@/lib/types'
import { Loader2, CheckCircle2, XCircle, Clock, ChevronRight, Trash2 } from 'lucide-react'

interface Props {
  jobs: SearchJob[]
  onSelect: (job: SearchJob) => void
  onDelete: (id: string) => void
  selectedId?: string
}

const STATUS_ICONS: Record<string, React.ReactNode> = {
  pending:   <Clock size={14} />,
  scraping:  <Loader2 size={14} className="animate-spin-slow" />,
  enriching: <Loader2 size={14} className="animate-spin-slow" />,
  verifying: <Loader2 size={14} className="animate-spin-slow" />,
  completed: <CheckCircle2 size={14} />,
  failed:    <XCircle size={14} />,
}

function timeAgo(dateStr: string): string {
  const diff = (Date.now() - new Date(dateStr).getTime()) / 1000
  if (diff < 60)  return `${Math.floor(diff)}s ago`
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  return `${Math.floor(diff / 86400)}d ago`
}

export default function JobHistory({ jobs, onSelect, onDelete, selectedId }: Props) {
  if (!jobs.length) return null

  return (
    <div className="card" style={{ borderRadius: 14 }}>
      <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)' }}>
        <h3 style={{ margin: 0, fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
          Recent Jobs
        </h3>
      </div>
      <div style={{ maxHeight: 360, overflowY: 'auto' }}>
        {jobs.map(job => (
          <div
            key={job.id}
            className="card-hover"
            onClick={() => onSelect(job)}
            style={{
              padding: '14px 20px',
              borderBottom: '1px solid rgba(99,102,241,0.08)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              background: selectedId === job.id ? 'rgba(99,102,241,0.08)' : 'transparent',
              transition: 'background 0.15s',
            }}
          >
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ fontWeight: 600, fontSize: '0.88rem', color: 'var(--text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {job.keyword}
                </span>
                <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>in {job.location}</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 4 }}>
                <span className={`badge badge-status ${job.status}`} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                  {STATUS_ICONS[job.status]}
                  {job.status}
                </span>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  {job.total_results} leads · {timeAgo(job.created_at)}
                </span>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <button
                onClick={e => { e.stopPropagation(); onDelete(job.id) }}
                style={{
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  color: 'var(--text-muted)',
                  padding: 4,
                  borderRadius: 6,
                  transition: 'color 0.15s',
                }}
                onMouseEnter={e => (e.currentTarget.style.color = 'var(--hot)')}
                onMouseLeave={e => (e.currentTarget.style.color = 'var(--text-muted)')}
                title="Delete job"
              >
                <Trash2 size={14} />
              </button>
              <ChevronRight size={16} style={{ color: 'var(--text-muted)' }} />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
