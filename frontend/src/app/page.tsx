'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { type SearchJob, type Lead, type WSMessage } from '@/lib/types'
import { getJobs, deleteJob, getExportUrl } from '@/lib/api'
import axios from 'axios'
import ResultsTable from '@/components/ResultsTable'
import ProgressBar from '@/components/ProgressBar'
import JobHistory from '@/components/JobHistory'
import CategoryPicker from '@/components/CategoryPicker'
import LocalityPicker from '@/components/LocalityPicker'
import KeywordPreview from '@/components/KeywordPreview'
import DropZone from '@/components/DropZone'
import { useNotifications } from '@/lib/useNotifications'
import {
  Zap, Activity, Users, TrendingUp, Wifi, WifiOff,
  Target, Globe2, Download, AlertTriangle, CheckCircle2,
  XCircle, Sliders, MapPin, Bell, BellOff, FileText,
  ChevronRight
} from 'lucide-react'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const WS_BASE = API.replace(/^http/, 'ws')

export default function Dashboard() {
  // ── Form State ───────────────────────────────────────────────────────────
  const [categories, setCategories] = useState<string[]>([])
  const [city, setCity] = useState('Mumbai')
  const [localities, setLocalities] = useState<string[]>([])
  const [selectAllLocalities, setSelectAllLocalities] = useState(false)
  const [leadGoal, setLeadGoal] = useState(50)
  const [previewKeywords, setPreviewKeywords] = useState<string[]>([])

  // ── App State ────────────────────────────────────────────────────────────
  const [jobs, setJobs] = useState<SearchJob[]>([])
  const [activeJob, setActiveJob] = useState<SearchJob | null>(null)
  const [leads, setLeads] = useState<Lead[]>([])
  const [tagFilter, setTagFilter] = useState<string>('all')
  const [searching, setSearching] = useState(false)
  const [wsConnected, setWsConnected] = useState(false)
  const [tagCounts, setTagCounts] = useState({ no_site: 0, fix_needed: 0, good_site: 0 })
  const [scrapingKeyword, setScrapingKeyword] = useState('')

  // ── File-job progress state ──────────────────────────────────────────────
  const [fileProgress, setFileProgress] = useState<{
    completedKw: number; totalKw: number; leadsFound: number; pct: number
  } | null>(null)
  const [notifPermission, setNotifPermission] = useState<NotificationPermission>('default')

  const wsRef = useRef<WebSocket | null>(null)
  const pollRef = useRef<NodeJS.Timeout | null>(null)

  // ── Notifications ────────────────────────────────────────────────────────
  const { requestPermission, notify } = useNotifications()

  useEffect(() => { loadJobs() }, [])
  useEffect(() => {
    if (typeof window !== 'undefined' && 'Notification' in window) {
      setNotifPermission(Notification.permission)
    }
  }, [])

  const handleRequestNotifPermission = async () => {
    const granted = await requestPermission()
    if (typeof window !== 'undefined' && 'Notification' in window) {
      setNotifPermission(Notification.permission)
    }
  }

  const loadJobs = async () => {
    try {
      const { jobs } = await getJobs()
      setJobs(jobs)
    } catch {}
  }

  const loadLeads = useCallback(async (jobId: string, tag?: string) => {
    try {
      const res = await axios.get(`${API}/api/search/${jobId}/leads`, {
        params: { page: 1, page_size: 300, tag: tag && tag !== 'all' ? tag : undefined }
      })
      setLeads(res.data.leads)
      setTagCounts({
        no_site: res.data.count_no_site,
        fix_needed: res.data.count_fix_needed,
        good_site: res.data.count_good_site,
      })
    } catch {}
  }, [])

  const startPolling = useCallback((jobId: string) => {
    if (pollRef.current) clearInterval(pollRef.current)
    pollRef.current = setInterval(async () => {
      try {
        const { jobs: fresh } = await getJobs()
        setJobs(fresh)
        const job = fresh.find(j => j.id === jobId)
        if (job) {
          setActiveJob(job)
          await loadLeads(jobId, tagFilter)
          if (job.status === 'completed' || job.status === 'failed') {
            clearInterval(pollRef.current!)
            setSearching(false)
          }
        }
      } catch {}
    }, 4000)
  }, [loadLeads, tagFilter])

  const connectWS = useCallback((jobId: string, totalKeywords?: number) => {
    if (wsRef.current) wsRef.current.close()
    const ws = new WebSocket(`${WS_BASE}/api/ws/${jobId}`)
    wsRef.current = ws
    ws.onopen = () => setWsConnected(true)
    ws.onerror = () => setWsConnected(false)

    ws.onmessage = ev => {
      const msg = JSON.parse(ev.data)

      if (msg.type === 'file_job_started') {
        // Notify: scraping started
        notify(
          {
            title: '⚡ LeadScout — Scraping started',
            body: `${msg.total_keywords} keywords queued · Goal: ${msg.lead_goal} leads`,
            tag: `job-start-${jobId}`,
          },
          'start'
        )
      }

      if (msg.type === 'file_progress') {
        setFileProgress({
          completedKw: msg.completed_keywords,
          totalKw: msg.total_keywords,
          leadsFound: msg.leads_found,
          pct: msg.pct,
        })
        // Send progress notification every 25%
        if (msg.pct % 25 === 0 && msg.pct > 0 && msg.pct < 100) {
          notify(
            {
              title: `📊 LeadScout — ${msg.pct}% complete`,
              body: `${msg.leads_found} leads found so far (${msg.completed_keywords}/${msg.total_keywords} keywords)`,
              tag: `job-progress-${jobId}-${msg.pct}`,
            },
            'progress'
          )
        }
      }

      if (msg.type === 'status') {
        setActiveJob(prev => prev ? { ...prev, status: msg.status } : prev)
        if (msg.status === 'completed') {
          setSearching(false)
          setFileProgress(null)
          loadLeads(jobId, tagFilter)
          loadJobs()
          // Final completion notification
          notify(
            {
              title: '🏆 LeadScout — Job Complete!',
              body: `${msg.total ?? 0} leads ready · Click to download your CSV`,
              tag: `job-done-${jobId}`,
              actionUrl: `${API}/api/search/${jobId}/export`,
            },
            'done'
          )
        } else if (msg.status === 'failed') {
          setSearching(false)
          setFileProgress(null)
          loadJobs()
        }
      } else if (msg.type === 'scraping_keyword') {
        setScrapingKeyword(msg.keyword)
      } else if (msg.type === 'lead_scraped') {
        setActiveJob(prev => prev ? { ...prev, total_results: msg.total } : prev)
        loadLeads(jobId, tagFilter)
      } else if (msg.type === 'lead_health' || msg.type === 'lead_enriched' || msg.type === 'lead_verified') {
        loadLeads(jobId, tagFilter)
      }
    }
    const ping = setInterval(() => { if (ws.readyState === WebSocket.OPEN) ws.send('ping') }, 20000)
    ws.onclose = () => { setWsConnected(false); clearInterval(ping) }
  }, [loadLeads, loadJobs, tagFilter, notify])

  const handleSearch = async () => {
    if (!city || categories.length === 0) return
    setSearching(true)
    setLeads([])
    setActiveJob(null)
    setScrapingKeyword('')
    setTagFilter('all')
    setFileProgress(null)

    try {
      const body = {
        keyword: categories[0],
        location: city,
        categories,
        localities: selectAllLocalities ? [] : localities,
        select_all_localities: selectAllLocalities,
        lead_goal: leadGoal,
        max_results: Math.min(leadGoal, 50),
      }
      const res = await axios.post(`${API}/api/search`, body)
      const job: SearchJob = res.data
      setActiveJob(job)
      setJobs(prev => [job, ...prev])

      notify(
        {
          title: '⚡ LeadScout — Scan launched',
          body: `Scraping "${categories[0]}" in ${city} · Goal: ${leadGoal} leads`,
          tag: `job-start-${job.id}`,
        },
        'start'
      )

      connectWS(job.id)
      startPolling(job.id)
    } catch (err) {
      setSearching(false)
      alert('Could not reach backend. Make sure FastAPI is running on port 8000.')
    }
  }

  // Called by DropZone after the backend accepted the upload
  const handleFileJobStarted = (jobId: string, totalKeywords: number) => {
    setSearching(true)
    setLeads([])
    setTagFilter('all')
    setScrapingKeyword('')
    setFileProgress({ completedKw: 0, totalKw: totalKeywords, leadsFound: 0, pct: 0 })

    // Create a synthetic job entry for the UI while real job loads
    const syntheticJob: SearchJob = {
      id: jobId,
      keyword: `File upload (${totalKeywords} keywords)`,
      location: city,
      localities: [],
      categories: [],
      lead_goal: leadGoal,
      status: 'pending',
      total_results: 0,
      processed_results: 0,
      error_message: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
    setActiveJob(syntheticJob)
    setJobs(prev => [syntheticJob, ...prev])

    connectWS(jobId, totalKeywords)
    startPolling(jobId)
    loadJobs()
  }

  const handleSelectJob = async (job: SearchJob) => {
    setActiveJob(job)
    setLeads([])
    setTagFilter('all')
    setFileProgress(null)
    setSearching(['scraping', 'health_check', 'enriching', 'verifying'].includes(job.status))
    await loadLeads(job.id, 'all')
    if (['scraping', 'health_check', 'enriching', 'verifying'].includes(job.status)) {
      connectWS(job.id)
      startPolling(job.id)
    }
  }

  const handleDeleteJob = async (id: string) => {
    await deleteJob(id)
    setJobs(prev => prev.filter(j => j.id !== id))
    if (activeJob?.id === id) { setActiveJob(null); setLeads([]) }
  }

  const handleTagFilter = async (tag: string) => {
    setTagFilter(tag)
    if (activeJob) await loadLeads(activeJob.id, tag)
  }

  // ── Stats ────────────────────────────────────────────────────────────────
  const totalLeads = activeJob?.total_results ?? leads.length
  const shownLeads = leads.length

  // ── Tag filter config ────────────────────────────────────────────────────
  const TAG_FILTERS = [
    { id: 'all',        label: 'All Leads',        count: totalLeads,          color: 'var(--accent)',  icon: '📋' },
    { id: 'NO_SITE',    label: '🏆 Golden Leads',   count: tagCounts.no_site,   color: 'var(--hot)',     icon: '🏆' },
    { id: 'FIX_NEEDED', label: '🔧 Fix Needed',     count: tagCounts.fix_needed, color: 'var(--warm)',   icon: '🔧' },
    { id: 'GOOD_SITE',  label: '✅ Good Sites',     count: tagCounts.good_site, color: '#10b981',        icon: '✅' },
  ]

  const canSearch = city && categories.length > 0 && !searching

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-deep)' }}>
      {/* ── Header ── */}
      <header className="glass" style={{ position: 'sticky', top: 0, zIndex: 50, borderBottom: '1px solid var(--border)', padding: '0 28px' }}>
        <div style={{ maxWidth: 1500, margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between', height: 60 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', borderRadius: 9, padding: 7, display: 'flex' }}>
              <Zap size={18} color="white" />
            </div>
            <div>
              <span style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
                Lead<span style={{ color: 'var(--accent)' }}>Scout</span>
              </span>
              <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', marginTop: -2 }}>Hyper-Local Lead Engine</div>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            {/* Notification permission button */}
            <button
              id="notif-permission-btn"
              onClick={handleRequestNotifPermission}
              title={notifPermission === 'granted' ? 'Desktop notifications: ON' : 'Enable desktop notifications'}
              style={{
                display: 'flex', alignItems: 'center', gap: 5,
                padding: '5px 10px', borderRadius: 8, border: '1px solid',
                fontSize: '0.72rem', fontWeight: 600, cursor: 'pointer',
                background: notifPermission === 'granted' ? 'rgba(16,185,129,0.1)' : 'rgba(99,102,241,0.1)',
                borderColor: notifPermission === 'granted' ? 'rgba(16,185,129,0.3)' : 'rgba(99,102,241,0.3)',
                color: notifPermission === 'granted' ? '#10b981' : 'var(--accent)',
              }}
            >
              {notifPermission === 'granted'
                ? <><Bell size={12} />Notifications ON</>
                : <><BellOff size={12} />Enable Alerts</>
              }
            </button>

            {activeJob && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: '0.78rem' }}>
                {wsConnected
                  ? <><Wifi size={12} style={{ color: '#10b981' }} /><span style={{ color: '#10b981' }}>Live</span></>
                  : <><WifiOff size={12} style={{ color: 'var(--text-muted)' }} /><span style={{ color: 'var(--text-muted)' }}>Polling</span></>}
              </div>
            )}
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              {jobs.length} jobs · {jobs.reduce((s, j) => s + j.total_results, 0)} leads
            </div>
          </div>
        </div>
      </header>

      <main style={{ maxWidth: 1500, margin: '0 auto', padding: '24px 20px', display: 'flex', gap: 20 }}>
        {/* ── Left: Builder Panel ── */}
        <aside style={{ flex: '0 0 360px', display: 'flex', flexDirection: 'column', gap: 16 }}>

          {/* ── Drop & Go Upload Zone ── */}
          <DropZone
            leadGoal={leadGoal}
            location={city}
            onJobStarted={handleFileJobStarted}
            disabled={searching}
          />

          {/* Search Builder */}
          <div className="card" style={{ borderRadius: 14, overflow: 'visible' }}>
            <div style={{ padding: '14px 18px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: 8 }}>
              <Sliders size={15} style={{ color: 'var(--accent)' }} />
              <span style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--text-primary)' }}>Manual Builder</span>
            </div>
            <div style={{ padding: 18, display: 'flex', flexDirection: 'column', gap: 18 }}>

              {/* Categories */}
              <CategoryPicker
                selectedCategories={categories}
                onChange={setCategories}
                disabled={searching}
              />

              {/* City + Localities */}
              <LocalityPicker
                city={city}
                onCityChange={setCity}
                selectedLocalities={localities}
                onLocalitiesChange={setLocalities}
                disabled={searching}
              />

              {/* Select all localities toggle */}
              {city && (
                <label style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer' }}>
                  <div
                    onClick={() => setSelectAllLocalities(v => !v)}
                    style={{
                      width: 36, height: 20, borderRadius: 10,
                      background: selectAllLocalities ? 'var(--accent)' : 'var(--border)',
                      position: 'relative', cursor: 'pointer', transition: 'background 0.2s',
                    }}
                  >
                    <div style={{
                      position: 'absolute', top: 2, left: selectAllLocalities ? 18 : 2,
                      width: 16, height: 16, borderRadius: '50%',
                      background: 'white', transition: 'left 0.2s',
                    }} />
                  </div>
                  <span style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', fontWeight: 600 }}>
                    Sweep ALL localities in {city}
                  </span>
                </label>
              )}

              {/* Lead Goal */}
              <div>
                <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Lead Goal
                </label>
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 8 }}>
                  {[30, 100, 250, 500, 1000].map(n => (
                    <button key={n} type="button" onClick={() => setLeadGoal(n)} disabled={searching}
                      style={{
                        flex: '1 1 auto', padding: '6px 8px', borderRadius: 7, fontSize: '0.78rem', fontWeight: 700,
                        cursor: 'pointer', border: '1px solid',
                        background: leadGoal === n ? 'rgba(99,102,241,0.2)' : 'transparent',
                        borderColor: leadGoal === n ? 'var(--accent)' : 'var(--border)',
                        color: leadGoal === n ? 'var(--accent)' : 'var(--text-muted)',
                        transition: 'all 0.15s',
                      }}>
                      {n >= 1000 ? `${n/1000}k` : n}
                    </button>
                  ))}
                </div>
                <input
                  type="number" min={1} max={5000}
                  value={leadGoal}
                  onChange={e => setLeadGoal(Number(e.target.value))}
                  disabled={searching}
                  className="input-field"
                  style={{ width: '100%' }}
                  placeholder="Custom number…"
                />
              </div>

              {/* Launch button */}
              <button
                id="launch-scan-btn"
                onClick={handleSearch}
                disabled={!canSearch}
                className="btn-primary"
                style={{ width: '100%', justifyContent: 'center', display: 'flex', alignItems: 'center', gap: 8, padding: '12px 0', fontSize: '0.95rem' }}
              >
                {searching ? (
                  <><div className="animate-spin-slow" style={{ width: 16, height: 16, border: '2px solid rgba(255,255,255,0.3)', borderTop: '2px solid white', borderRadius: '50%' }} />
                    Scanning…</>
                ) : (
                  <><Zap size={17} /> Launch Scan ({leadGoal} leads)</>
                )}
              </button>

              {!canSearch && !searching && (
                <p style={{ margin: 0, fontSize: '0.75rem', color: 'var(--text-muted)', textAlign: 'center' }}>
                  Select at least 1 category + city to start
                </p>
              )}
            </div>
          </div>

          {/* Keyword Preview */}
          <KeywordPreview
            categories={categories}
            city={city}
            localities={selectAllLocalities ? [] : localities}
            selectAllLocalities={selectAllLocalities}
            onChange={setPreviewKeywords}
          />

          {/* Job History */}
          <JobHistory
            jobs={jobs}
            onSelect={handleSelectJob}
            onDelete={handleDeleteJob}
            selectedId={activeJob?.id}
          />
        </aside>

        {/* ── Right: Results ── */}
        <div style={{ flex: '1 1 640px', display: 'flex', flexDirection: 'column', gap: 16, minWidth: 0 }}>

          {activeJob ? (
            <>
              {/* Job header + progress */}
              <div className="card" style={{ borderRadius: 14, overflow: 'hidden' }}>
                <div style={{ padding: '14px 18px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <h2 style={{ margin: 0, fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {activeJob.keyword}
                      <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}> · </span>
                      <MapPin size={13} style={{ display: 'inline', verticalAlign: 'middle', color: 'var(--accent)' }} />
                      {' '}{activeJob.location}
                    </h2>
                    {scrapingKeyword && searching && (
                      <p style={{ margin: '2px 0 0', fontSize: '0.72rem', color: 'var(--warm)' }}>
                        ● {scrapingKeyword}
                      </p>
                    )}
                  </div>
                </div>

                {/* File-job progress bar */}
                {fileProgress && searching && (
                  <div style={{ padding: '10px 18px', background: 'rgba(99,102,241,0.06)', borderBottom: '1px solid var(--border)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <FileText size={13} style={{ color: 'var(--accent)' }} />
                        <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                          Keyword file processing
                        </span>
                      </div>
                      <div style={{ display: 'flex', gap: 14, fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                        <span><span style={{ color: 'var(--accent)', fontWeight: 700 }}>{fileProgress.completedKw}</span>/{fileProgress.totalKw} keywords</span>
                        <span><span style={{ color: '#10b981', fontWeight: 700 }}>{fileProgress.leadsFound}</span> leads</span>
                        <span style={{ color: 'var(--accent)', fontWeight: 700 }}>{fileProgress.pct}%</span>
                      </div>
                    </div>
                    <div style={{ background: 'var(--bg-panel)', borderRadius: 999, height: 5, overflow: 'hidden' }}>
                      <div style={{
                        height: '100%', borderRadius: 999,
                        background: 'linear-gradient(90deg,#6366f1,#8b5cf6)',
                        width: `${fileProgress.pct}%`,
                        transition: 'width 0.6s ease',
                        boxShadow: '0 0 8px rgba(99,102,241,0.5)',
                      }} />
                    </div>
                    {/* Keyword batch indicator */}
                    <div style={{ marginTop: 6, display: 'flex', gap: 3, flexWrap: 'wrap' }}>
                      {Array.from({ length: Math.min(fileProgress.totalKw, 20) }).map((_, i) => (
                        <div key={i} style={{
                          width: 6, height: 6, borderRadius: '50%',
                          background: i < Math.round(fileProgress.completedKw / fileProgress.totalKw * Math.min(fileProgress.totalKw, 20))
                            ? '#6366f1' : 'var(--border)',
                          transition: 'background 0.3s',
                        }} />
                      ))}
                      {fileProgress.totalKw > 20 && (
                        <span style={{ fontSize: '0.6rem', color: 'var(--text-muted)', alignSelf: 'center' }}>+{fileProgress.totalKw - 20} more</span>
                      )}
                    </div>
                  </div>
                )}

                <ProgressBar job={activeJob} />
              </div>

              {/* Segmented filter + export buttons */}
              <div className="card" style={{ borderRadius: 12, padding: '14px 16px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
                  <span style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>Show:</span>
                  {TAG_FILTERS.map(f => (
                    <button
                      key={f.id}
                      onClick={() => handleTagFilter(f.id)}
                      style={{
                        flex: '1 1 auto', padding: '6px 12px', borderRadius: 8, fontSize: '0.78rem', fontWeight: 600,
                        cursor: 'pointer', border: '1px solid',
                        background: tagFilter === f.id ? `${f.color}22` : 'transparent',
                        borderColor: tagFilter === f.id ? f.color : 'var(--border)',
                        color: tagFilter === f.id ? f.color : 'var(--text-muted)',
                        transition: 'all 0.15s', whiteSpace: 'nowrap',
                        display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 5,
                      }}>
                      {f.label}
                      {f.count > 0 && (
                        <span style={{ background: tagFilter === f.id ? f.color : 'var(--border)', borderRadius: 10, padding: '0 5px', fontSize: '0.65rem', color: tagFilter === f.id ? 'white' : 'var(--text-muted)' }}>
                          {f.count}
                        </span>
                      )}
                    </button>
                  ))}

                  <div style={{ marginLeft: 'auto', display: 'flex', gap: 6 }}>
                    {TAG_FILTERS.filter(f => f.id !== 'all').map(f => (
                      <a
                        key={f.id}
                        href={`${API}/api/search/${activeJob.id}/export?tag=${f.id}`}
                        download
                        style={{
                          padding: '6px 10px', borderRadius: 7, fontSize: '0.72rem', fontWeight: 700,
                          textDecoration: 'none', border: '1px solid',
                          background: 'transparent', borderColor: 'var(--border)',
                          color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 4,
                          transition: 'all 0.15s',
                        }}
                        onMouseEnter={e => { e.currentTarget.style.borderColor = f.color; e.currentTarget.style.color = f.color }}
                        onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.color = 'var(--text-muted)' }}
                        title={`Export ${f.label}`}
                      >
                        <Download size={11} />
                        {f.id === 'NO_SITE' ? 'Golden' : f.id === 'FIX_NEEDED' ? 'Fix' : 'Good'}
                      </a>
                    ))}
                    <a
                      id="export-all-btn"
                      href={`${API}/api/search/${activeJob.id}/export`}
                      download
                      style={{
                        padding: '6px 12px', borderRadius: 7, fontSize: '0.78rem', fontWeight: 700,
                        textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 5,
                        background: 'linear-gradient(135deg, #10b981, #059669)', color: 'white', border: 'none',
                      }}>
                      <Download size={13} /> Export All
                    </a>
                  </div>
                </div>
              </div>

              {/* Stats row */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
                {[
                  { icon: <Users size={16} />, label: 'Total Found', value: totalLeads, color: 'var(--accent)' },
                  { icon: <XCircle size={16} />, label: 'No Website 🏆', value: tagCounts.no_site, color: 'var(--hot)', sub: 'Golden leads' },
                  { icon: <AlertTriangle size={16} />, label: 'Fix Needed', value: tagCounts.fix_needed, color: 'var(--warm)', sub: 'Optim. leads' },
                  { icon: <CheckCircle2 size={16} />, label: 'Good Sites', value: tagCounts.good_site, color: '#10b981', sub: 'Healthy' },
                ].map(stat => (
                  <div key={stat.label} className="card" style={{ borderRadius: 11, padding: '14px 16px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <div style={{ color: stat.color, opacity: 0.8 }}>{stat.icon}</div>
                      <div>
                        <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>{stat.label}</div>
                        <div style={{ fontSize: '1.4rem', fontWeight: 800, color: stat.color, lineHeight: 1.1 }}>{stat.value}</div>
                        {stat.sub && <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>{stat.sub}</div>}
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Results Table */}
              <div className="card" style={{ borderRadius: 14, overflow: 'hidden' }}>
                <div style={{ padding: '12px 18px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Activity size={15} style={{ color: 'var(--accent)' }} />
                  <h3 style={{ margin: 0, fontSize: '0.88rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                    {TAG_FILTERS.find(f => f.id === tagFilter)?.label || 'All Leads'}
                  </h3>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>({shownLeads} shown)</span>
                  {searching && <span style={{ fontSize: '0.72rem', color: 'var(--warm)', marginLeft: 8 }}>● Live updating…</span>}
                </div>
                <ResultsTable leads={leads} loading={searching} />
              </div>
            </>
          ) : (
            /* Empty state */
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: 60, textAlign: 'center' }}>
              <div style={{ width: 90, height: 90, background: 'linear-gradient(135deg, rgba(99,102,241,0.2), rgba(139,92,246,0.2))', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 28, fontSize: '2.2rem' }}>⚡</div>
              <h2 style={{ margin: '0 0 10px', fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-primary)' }}>Hyper-Local Lead Engine</h2>
              <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '0.9rem', maxWidth: 440, lineHeight: 1.7 }}>
                <strong style={{ color: 'var(--accent)' }}>Drop &amp; Go:</strong> Upload a .txt file with one keyword per line, click <em>Upload &amp; Start Scraping</em>, and walk away.<br />
                Or use the manual builder below to pick categories and localities.
              </p>
              <div style={{ marginTop: 36, display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, maxWidth: 600 }}>
                {[
                  { emoji: '📂', title: 'Drop & Go', desc: 'Upload .txt → auto-queue' },
                  { emoji: '🏆', title: 'Golden Leads', desc: 'No website — easiest clients' },
                  { emoji: '🔔', title: 'Desktop Alerts', desc: 'OS-level notifications' },
                  { emoji: '📍', title: '57 Localities', desc: 'Mumbai + 5 major cities' },
                ].map(f => (
                  <div key={f.title} className="card" style={{ padding: '16px 12px', textAlign: 'center', borderRadius: 12 }}>
                    <div style={{ fontSize: '1.8rem', marginBottom: 7 }}>{f.emoji}</div>
                    <div style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-primary)' }}>{f.title}</div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: 3 }}>{f.desc}</div>
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
