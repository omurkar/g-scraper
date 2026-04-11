'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { type SearchJob, type Lead, type WSMessage } from '@/lib/types'
import { createSearch, getLeads, getJobs, deleteJob } from '@/lib/api'
import SearchBar from '@/components/SearchBar'
import ResultsTable from '@/components/ResultsTable'
import ProgressBar from '@/components/ProgressBar'
import ExportButton from '@/components/ExportButton'
import JobHistory from '@/components/JobHistory'
import { Zap, Activity, Users, TrendingUp, Wifi, WifiOff } from 'lucide-react'

const WS_BASE = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/^http/, 'ws')

export default function Dashboard() {
  const [jobs, setJobs] = useState<SearchJob[]>([])
  const [activeJob, setActiveJob] = useState<SearchJob | null>(null)
  const [leads, setLeads] = useState<Lead[]>([])
  const [searching, setSearching] = useState(false)
  const [wsConnected, setWsConnected] = useState(false)

  const wsRef = useRef<WebSocket | null>(null)
  const pollRef = useRef<NodeJS.Timeout | null>(null)

  // ── Load jobs on mount ───────────────────────────────────────────────────
  useEffect(() => {
    loadJobs()
  }, [])

  const loadJobs = async () => {
    try {
      const { jobs } = await getJobs()
      setJobs(jobs)
    } catch { /* backend may not be running */ }
  }

  // ── Load leads for active job ────────────────────────────────────────────
  const loadLeads = useCallback(async (jobId: string) => {
    try {
      const res = await getLeads(jobId, 1, 200)
      setLeads(res.leads)
    } catch {}
  }, [])

  // ── Polling for active job ───────────────────────────────────────────────
  const startPolling = useCallback((jobId: string) => {
    if (pollRef.current) clearInterval(pollRef.current)
    pollRef.current = setInterval(async () => {
      try {
        const { jobs: fresh } = await getJobs()
        setJobs(fresh)
        const job = fresh.find(j => j.id === jobId)
        if (job) {
          setActiveJob(job)
          await loadLeads(jobId)
          if (job.status === 'completed' || job.status === 'failed') {
            clearInterval(pollRef.current!)
            setSearching(false)
          }
        }
      } catch {}
    }, 3000)
  }, [loadLeads])

  // ── WebSocket connection ─────────────────────────────────────────────────
  const connectWS = useCallback((jobId: string) => {
    if (wsRef.current) wsRef.current.close()
    const ws = new WebSocket(`${WS_BASE}/api/ws/${jobId}`)
    wsRef.current = ws

    ws.onopen = () => setWsConnected(true)
    ws.onclose = () => setWsConnected(false)
    ws.onerror = () => setWsConnected(false)

    ws.onmessage = (event) => {
      const msg: WSMessage = JSON.parse(event.data)

      if (msg.type === 'status') {
        setActiveJob(prev => prev ? { ...prev, status: msg.status as SearchJob['status'], total_results: msg.total ?? prev.total_results } : prev)
        if (msg.status === 'completed' || msg.status === 'failed') {
          setSearching(false)
          loadLeads(jobId)
          loadJobs()
        }
      } else if (msg.type === 'lead_scraped') {
        setLeads(prev => {
          if (prev.find(l => l.id === msg.lead.id)) return prev
          return [...prev, msg.lead]
        })
        setActiveJob(prev => prev ? { ...prev, total_results: msg.total } : prev)
      } else if (msg.type === 'lead_enriched') {
        loadLeads(jobId)
      } else if (msg.type === 'lead_verified') {
        loadLeads(jobId)
      }
    }

    // Keep-alive pings
    const ping = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) ws.send('ping')
    }, 20000)
    ws.onclose = () => { setWsConnected(false); clearInterval(ping) }
  }, [loadLeads, loadJobs])

  // ── New search ───────────────────────────────────────────────────────────
  const handleSearch = async (keyword: string, location: string) => {
    setSearching(true)
    setLeads([])
    setActiveJob(null)

    try {
      const job = await createSearch(keyword, location, 30)
      setActiveJob(job)
      setJobs(prev => [job, ...prev])
      connectWS(job.id)
      startPolling(job.id)
    } catch (err) {
      console.error('Search failed:', err)
      setSearching(false)
      alert('Could not connect to backend. Make sure the FastAPI server is running on port 8000.')
    }
  }

  // ── Select job from history ──────────────────────────────────────────────
  const handleSelectJob = async (job: SearchJob) => {
    setActiveJob(job)
    setLeads([])
    setSearching(['scraping', 'enriching', 'verifying'].includes(job.status))
    await loadLeads(job.id)
    if (['scraping', 'enriching', 'verifying'].includes(job.status)) {
      connectWS(job.id)
      startPolling(job.id)
    }
  }

  const handleDeleteJob = async (id: string) => {
    await deleteJob(id)
    setJobs(prev => prev.filter(j => j.id !== id))
    if (activeJob?.id === id) {
      setActiveJob(null)
      setLeads([])
    }
  }

  // ── Stats ────────────────────────────────────────────────────────────────
  const totalLeads = leads.length
  const hotLeads   = leads.filter(l => l.verification?.quality_score === 'hot').length
  const withEmail  = leads.filter(l => (l.enrichment?.emails?.length ?? 0) > 0).length
  const enrichPct  = totalLeads > 0 ? Math.round((withEmail / totalLeads) * 100) : 0

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-deep)' }}>
      {/* ── Header ── */}
      <header className="glass" style={{
        position: 'sticky', top: 0, zIndex: 50,
        borderBottom: '1px solid var(--border)',
        padding: '0 32px',
      }}>
        <div style={{ maxWidth: 1400, margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between', height: 64 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{
              background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
              borderRadius: 10,
              padding: 8,
              display: 'flex',
            }}>
              <Zap size={20} color="white" />
            </div>
            <div>
              <span style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
                Lead<span style={{ color: 'var(--accent)' }}>Scout</span>
              </span>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: -2 }}>
                AI-Powered Lead Generation
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            {activeJob && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.8rem' }}>
                {wsConnected
                  ? <><Wifi size={13} style={{ color: '#10b981' }} /><span style={{ color: '#10b981' }}>Live</span></>
                  : <><WifiOff size={13} style={{ color: 'var(--text-muted)' }} /><span style={{ color: 'var(--text-muted)' }}>Polling</span></>
                }
              </div>
            )}
            <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              {jobs.length} jobs · {jobs.reduce((s, j) => s + j.total_results, 0)} leads
            </div>
          </div>
        </div>
      </header>

      <main style={{ maxWidth: 1400, margin: '0 auto', padding: '32px 24px', display: 'flex', gap: 24, flexWrap: 'wrap' }}>
        {/* ── Left sidebar ── */}
        <aside style={{ flex: '0 0 320px', display: 'flex', flexDirection: 'column', gap: 20 }}>
          <SearchBar onSearch={handleSearch} loading={searching} />
          <JobHistory
            jobs={jobs}
            onSelect={handleSelectJob}
            onDelete={handleDeleteJob}
            selectedId={activeJob?.id}
          />
        </aside>

        {/* ── Main panel ── */}
        <div style={{ flex: '1 1 640px', display: 'flex', flexDirection: 'column', gap: 20, minWidth: 0 }}>

          {activeJob ? (
            <>
              {/* Job header */}
              <div className="card" style={{ borderRadius: 14, overflow: 'hidden' }}>
                <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
                  <div>
                    <h2 style={{ margin: 0, fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                      {activeJob.keyword}
                      <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}> in </span>
                      {activeJob.location}
                    </h2>
                    <p style={{ margin: '2px 0 0', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                      Job ID: {activeJob.id.slice(0, 8)}…
                    </p>
                  </div>
                  <ExportButton
                    jobId={activeJob.id}
                    totalLeads={totalLeads}
                    disabled={searching}
                  />
                </div>
                <ProgressBar job={activeJob} />
              </div>

              {/* Stats row */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 14 }}>
                {[
                  { icon: <Users size={18} />, label: 'Total Leads', value: totalLeads, color: 'var(--accent)' },
                  { icon: <Activity size={18} />, label: 'With Email', value: `${withEmail} (${enrichPct}%)`, color: '#10b981' },
                  { icon: <TrendingUp size={18} />, label: 'Hot Leads 🔥', value: hotLeads, color: 'var(--hot)' },
                  { icon: <Zap size={18} />, label: 'Status', value: activeJob.status.charAt(0).toUpperCase() + activeJob.status.slice(1), color: 'var(--warm)' },
                ].map(stat => (
                  <div key={stat.label} className="card" style={{ borderRadius: 12, padding: '16px 18px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <div style={{ color: stat.color, opacity: 0.8 }}>{stat.icon}</div>
                      <div>
                        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                          {stat.label}
                        </div>
                        <div style={{ fontSize: '1.2rem', fontWeight: 800, color: stat.color, marginTop: 2 }}>
                          {stat.value}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Results table */}
              <div className="card" style={{ borderRadius: 14, overflow: 'hidden' }}>
                <div style={{ padding: '14px 20px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Activity size={16} style={{ color: 'var(--accent)' }} />
                  <h3 style={{ margin: 0, fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                    Lead Results
                  </h3>
                  {searching && <span style={{ fontSize: '0.75rem', color: 'var(--warm)', marginLeft: 8 }}>● Live updating…</span>}
                </div>
                <ResultsTable leads={leads} loading={searching} />
              </div>
            </>
          ) : (
            /* Empty state */
            <div style={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              padding: 64,
              textAlign: 'center',
            }}>
              <div style={{
                width: 80, height: 80,
                background: 'linear-gradient(135deg, rgba(99,102,241,0.2), rgba(139,92,246,0.2))',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: 24,
                fontSize: '2rem',
              }}>
                ⚡
              </div>
              <h2 style={{ margin: '0 0 10px', fontSize: '1.4rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                Ready to find leads
              </h2>
              <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '0.9rem', maxWidth: 360, lineHeight: 1.6 }}>
                Enter a business type and location in the search bar to start scraping Google Maps,
                enriching with contact info, and verifying with AI.
              </p>
              <div style={{ marginTop: 32, display: 'flex', gap: 20, flexWrap: 'wrap', justifyContent: 'center' }}>
                {[
                  { emoji: '🗺️', title: 'Google Maps', desc: 'Scrape business data' },
                  { emoji: '📧', title: 'Email Finder', desc: 'Extract contact info' },
                  { emoji: '🤖', title: 'AI Verify', desc: 'Gemini quality scoring' },
                  { emoji: '📊', title: 'CSV Export', desc: 'Download your leads' },
                ].map(f => (
                  <div key={f.title} className="card" style={{ width: 130, padding: '18px 14px', textAlign: 'center', borderRadius: 12 }}>
                    <div style={{ fontSize: '1.6rem', marginBottom: 8 }}>{f.emoji}</div>
                    <div style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-primary)' }}>{f.title}</div>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: 3 }}>{f.desc}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
