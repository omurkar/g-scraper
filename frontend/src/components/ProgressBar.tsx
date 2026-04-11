'use client'

import { type SearchJob } from '@/lib/types'
import { Loader2, CheckCircle2, XCircle, Clock } from 'lucide-react'

interface Props {
  job: SearchJob
}

const PHASES = ['scraping', 'enriching', 'verifying', 'completed']

function phaseIndex(status: string): number {
  return PHASES.indexOf(status)
}

export default function ProgressBar({ job }: Props) {
  if (job.status === 'pending') {
    return (
      <div style={{ padding: '12px 16px', display: 'flex', alignItems: 'center', gap: 8, color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
        <Clock size={14} />
        Queued — starting soon…
      </div>
    )
  }

  if (job.status === 'failed') {
    return (
      <div style={{ padding: '12px 16px', display: 'flex', alignItems: 'center', gap: 8, color: 'var(--hot)', fontSize: '0.85rem' }}>
        <XCircle size={14} />
        Failed: {job.error_message || 'Unknown error'}
      </div>
    )
  }

  if (job.status === 'completed') {
    return (
      <div style={{ padding: '12px 16px', display: 'flex', alignItems: 'center', gap: 8 }}>
        <CheckCircle2 size={16} style={{ color: '#10b981' }} />
        <span style={{ color: '#10b981', fontWeight: 600, fontSize: '0.88rem' }}>
          Completed — {job.total_results} leads found
        </span>
      </div>
    )
  }

  const currentPhase = phaseIndex(job.status)
  const pct = job.total_results > 0
    ? Math.round((job.processed_results / job.total_results) * 100)
    : 0

  return (
    <div style={{ padding: '12px 16px' }}>
      {/* Phase steps */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 0, marginBottom: 10 }}>
        {['Scraping', 'Enriching', 'Verifying', 'Done'].map((label, i) => {
          const done = i < currentPhase || job.status === 'completed'
          const active = label.toLowerCase() === job.status || (label === 'Done' && job.status === 'completed')
          return (
            <div key={label} style={{ display: 'flex', alignItems: 'center', flex: i < 3 ? 1 : undefined }}>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: 4,
                fontSize: '0.75rem',
                fontWeight: active ? 700 : 500,
                color: done || active ? 'var(--accent)' : 'var(--text-muted)',
                whiteSpace: 'nowrap',
              }}>
                {done && !active ? <CheckCircle2 size={12} /> : active ? <Loader2 size={12} className="animate-spin-slow" /> : <span style={{ width: 12, height: 12, borderRadius: '50%', background: 'var(--border)', display: 'inline-block' }} />}
                {label}
              </div>
              {i < 3 && (
                <div style={{
                  flex: 1,
                  height: 1,
                  margin: '0 6px',
                  background: done ? 'var(--accent)' : 'var(--border)',
                  transition: 'background 0.5s',
                }} />
              )}
            </div>
          )
        })}
      </div>

      {/* Progress bar */}
      <div className="progress-bar-track">
        <div className="progress-bar-fill" style={{ width: `${pct}%` }} />
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 4, fontSize: '0.75rem', color: 'var(--text-muted)' }}>
        <span>{job.processed_results} / {job.total_results || '?'} leads</span>
        <span>{pct}%</span>
      </div>
    </div>
  )
}
