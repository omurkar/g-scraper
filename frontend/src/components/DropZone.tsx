'use client'

import { useCallback, useRef, useState, DragEvent, ChangeEvent } from 'react'
import { Upload, FileText, Zap, X, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react'
import axios from 'axios'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type DropZoneState = 'idle' | 'dragging' | 'parsing' | 'uploading' | 'success' | 'error'

interface DropZoneProps {
  leadGoal: number
  location?: string
  onJobStarted: (jobId: string, totalKeywords: number) => void
  disabled?: boolean
}

export default function DropZone({
  leadGoal,
  location = 'India',
  onJobStarted,
  disabled = false,
}: DropZoneProps) {
  const [state, setState] = useState<DropZoneState>('idle')
  const [parsedKeywords, setParsedKeywords] = useState<string[]>([])
  const [fileName, setFileName] = useState('')
  const [error, setError] = useState('')
  const [uploadPct, setUploadPct] = useState(0)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const fileRef = useRef<File | null>(null)

  // ── Parse the .txt file locally for preview ──────────────────────────────
  const parseFile = useCallback((file: File) => {
    if (!file.name.endsWith('.txt')) {
      setState('error')
      setError('Only .txt files are supported. Please upload a plain text file.')
      return
    }
    fileRef.current = file
    setFileName(file.name)
    setState('parsing')
    const reader = new FileReader()
    reader.onload = (e) => {
      const text = (e.target?.result as string) ?? ''
      const kws = text
        .split('\n')
        .map((l) => l.trim())
        .filter((l) => l && !l.startsWith('#'))
      if (kws.length === 0) {
        setState('error')
        setError('No valid keywords found. Make sure your file has one keyword per line.')
        return
      }
      setParsedKeywords(kws)
      setState('idle') // show the preview + "Upload & Start" button
    }
    reader.readAsText(file)
  }, [])

  // ── Drag handlers ──────────────────────────────────────────────────────────
  const onDragOver = (e: DragEvent<HTMLDivElement>) => { e.preventDefault(); setState('dragging') }
  const onDragLeave = () => { if (state === 'dragging') setState(parsedKeywords.length ? 'idle' : 'idle') }
  const onDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    const file = e.dataTransfer.files?.[0]
    if (file) parseFile(file)
  }
  const onFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) parseFile(file)
    e.target.value = '' // reset so same file can be re-selected
  }

  // ── Upload & Start ─────────────────────────────────────────────────────────
  const handleUploadAndStart = async () => {
    if (!fileRef.current || parsedKeywords.length === 0) return
    setState('uploading')
    setUploadPct(0)
    setError('')

    try {
      const form = new FormData()
      form.append('file', fileRef.current)

      const res = await axios.post(
        `${API}/api/upload-keywords?lead_goal=${leadGoal}&location=${encodeURIComponent(location)}`,
        form,
        {
          headers: { 'Content-Type': 'multipart/form-data' },
          onUploadProgress: (e) => {
            if (e.total) setUploadPct(Math.round((e.loaded / e.total) * 100))
          },
        }
      )

      setState('success')
      onJobStarted(res.data.job_id, res.data.total_keywords)
    } catch (err: any) {
      setState('error')
      setError(err?.response?.data?.detail ?? 'Upload failed — check that the backend is running.')
    }
  }

  const handleReset = () => {
    setState('idle')
    setParsedKeywords([])
    setFileName('')
    setError('')
    setUploadPct(0)
    fileRef.current = null
  }

  const isDragging = state === 'dragging'
  const hasFile = parsedKeywords.length > 0 && state !== 'success' && state !== 'error'
  const isUploading = state === 'uploading'

  return (
    <div
      style={{
        background: 'var(--bg-card)',
        border: `1.5px dashed ${isDragging ? '#6366f1' : state === 'success' ? '#10b981' : state === 'error' ? '#ef4444' : 'rgba(99,102,241,0.35)'}`,
        borderRadius: 14,
        transition: 'all 0.2s',
        boxShadow: isDragging ? '0 0 0 4px rgba(99,102,241,0.15), 0 0 30px rgba(99,102,241,0.2)' : 'none',
        overflow: 'hidden',
      }}
      onDragOver={!disabled ? onDragOver : undefined}
      onDragLeave={!disabled ? onDragLeave : undefined}
      onDrop={!disabled ? onDrop : undefined}
    >
      {/* Header */}
      <div
        style={{
          padding: '12px 16px',
          borderBottom: '1px solid var(--border)',
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          background: 'rgba(99,102,241,0.06)',
        }}
      >
        <div style={{ background: 'linear-gradient(135deg,#6366f1,#8b5cf6)', borderRadius: 7, padding: 5, display: 'flex' }}>
          <Zap size={13} color="white" />
        </div>
        <span style={{ fontWeight: 700, fontSize: '0.85rem', color: 'var(--text-primary)' }}>
          Drop &amp; Go Upload
        </span>
        <span style={{ marginLeft: 'auto', fontSize: '0.7rem', color: 'var(--text-muted)', background: 'rgba(99,102,241,0.12)', padding: '2px 8px', borderRadius: 20, border: '1px solid rgba(99,102,241,0.2)' }}>
          .txt only
        </span>
      </div>

      <div style={{ padding: 16 }}>
        {/* ── Success ── */}
        {state === 'success' && (
          <div style={{ textAlign: 'center', padding: '12px 0' }}>
            <CheckCircle2 size={32} style={{ color: '#10b981', marginBottom: 8 }} />
            <div style={{ fontWeight: 700, color: '#10b981', fontSize: '0.9rem' }}>Job Queued!</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 4 }}>
              {parsedKeywords.length} keywords — scraping in progress
            </div>
            <button
              onClick={handleReset}
              style={{ marginTop: 12, fontSize: '0.75rem', color: 'var(--text-muted)', background: 'none', border: '1px solid var(--border)', borderRadius: 8, padding: '5px 14px', cursor: 'pointer' }}
            >
              Upload another file
            </button>
          </div>
        )}

        {/* ── Error ── */}
        {state === 'error' && (
          <div style={{ textAlign: 'center', padding: '10px 0' }}>
            <AlertCircle size={28} style={{ color: '#ef4444', marginBottom: 8 }} />
            <div style={{ fontSize: '0.78rem', color: '#ef4444', marginBottom: 12 }}>{error}</div>
            <button
              onClick={handleReset}
              style={{ fontSize: '0.75rem', color: 'var(--text-muted)', background: 'none', border: '1px solid var(--border)', borderRadius: 8, padding: '5px 14px', cursor: 'pointer' }}
            >
              Try again
            </button>
          </div>
        )}

        {/* ── Uploading progress ── */}
        {isUploading && (
          <div style={{ textAlign: 'center', padding: '12px 0' }}>
            <Loader2 size={28} style={{ color: 'var(--accent)', marginBottom: 8, animation: 'spin-slow 1.2s linear infinite' }} />
            <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.85rem', marginBottom: 8 }}>
              Uploading &amp; queuing jobs…
            </div>
            <div style={{ background: 'var(--bg-panel)', borderRadius: 999, height: 6, overflow: 'hidden' }}>
              <div style={{ height: '100%', background: 'linear-gradient(90deg,#6366f1,#8b5cf6)', borderRadius: 999, width: `${uploadPct}%`, transition: 'width 0.3s' }} />
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: 5 }}>{uploadPct}%</div>
          </div>
        )}

        {/* ── File preview with Upload & Start button ── */}
        {hasFile && !isUploading && (
          <div>
            {/* File info strip */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10, background: 'var(--bg-panel)', borderRadius: 10, padding: '8px 12px' }}>
              <FileText size={15} style={{ color: 'var(--accent)', flexShrink: 0 }} />
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{fileName}</div>
                <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>
                  {parsedKeywords.length} keyword{parsedKeywords.length !== 1 ? 's' : ''} detected
                </div>
              </div>
              <button onClick={handleReset} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', display: 'flex', padding: 4 }}>
                <X size={13} />
              </button>
            </div>

            {/* Total Jobs badge */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Total Jobs</span>
              <span style={{ fontSize: '0.78rem', fontWeight: 800, color: 'var(--accent)', background: 'rgba(99,102,241,0.12)', padding: '2px 10px', borderRadius: 20, border: '1px solid rgba(99,102,241,0.25)' }}>
                {parsedKeywords.length}
              </span>
            </div>

            {/* Keyword preview list (max 5 visible) */}
            <div style={{ marginBottom: 12, fontSize: '0.7rem', color: 'var(--text-muted)', background: 'var(--bg-panel)', borderRadius: 8, padding: '8px 10px', maxHeight: 90, overflowY: 'auto' }}>
              {parsedKeywords.slice(0, 8).map((kw, i) => (
                <div key={i} style={{ padding: '2px 0', borderBottom: i < Math.min(7, parsedKeywords.length - 1) ? '1px solid rgba(255,255,255,0.04)' : 'none', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  <span style={{ color: 'rgba(99,102,241,0.6)', marginRight: 5 }}>#{i + 1}</span>{kw}
                </div>
              ))}
              {parsedKeywords.length > 8 && (
                <div style={{ color: 'rgba(99,102,241,0.5)', paddingTop: 4 }}>+{parsedKeywords.length - 8} more…</div>
              )}
            </div>

            {/* Upload & Start Scraping button */}
            <button
              id="upload-and-start-btn"
              onClick={handleUploadAndStart}
              disabled={disabled}
              style={{
                width: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 8,
                padding: '11px 0',
                borderRadius: 10,
                border: 'none',
                background: disabled ? 'var(--bg-panel)' : 'linear-gradient(135deg,#6366f1,#8b5cf6)',
                color: disabled ? 'var(--text-muted)' : 'white',
                fontWeight: 700,
                fontSize: '0.88rem',
                cursor: disabled ? 'not-allowed' : 'pointer',
                transition: 'all 0.2s',
                boxShadow: disabled ? 'none' : '0 4px 18px rgba(99,102,241,0.35)',
              }}
              onMouseEnter={e => { if (!disabled) (e.currentTarget.style.opacity = '0.9') }}
              onMouseLeave={e => { (e.currentTarget.style.opacity = '1') }}
            >
              <Zap size={15} />
              Upload &amp; Start Scraping ({parsedKeywords.length} jobs)
            </button>
          </div>
        )}

        {/* ── Drop zone (idle, no file) ── */}
        {!hasFile && !isUploading && state !== 'success' && state !== 'error' && (
          <div
            style={{ textAlign: 'center', padding: '18px 12px', cursor: disabled ? 'not-allowed' : 'pointer' }}
            onClick={() => !disabled && fileInputRef.current?.click()}
          >
            <div style={{
              width: 48, height: 48,
              background: isDragging ? 'rgba(99,102,241,0.2)' : 'rgba(99,102,241,0.08)',
              borderRadius: '50%',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              margin: '0 auto 10px',
              transition: 'all 0.2s',
              transform: isDragging ? 'scale(1.12)' : 'scale(1)',
            }}>
              <Upload size={20} style={{ color: isDragging ? '#818cf8' : 'var(--accent)' }} />
            </div>
            <div style={{ fontSize: '0.82rem', fontWeight: 600, color: isDragging ? '#818cf8' : 'var(--text-primary)', marginBottom: 4 }}>
              {isDragging ? 'Drop it!' : 'Drag & drop your keywords.txt'}
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>
              One keyword per line · supports "Category in City" · no limit
            </div>
            <button
              onClick={(e) => { e.stopPropagation(); if (!disabled) fileInputRef.current?.click() }}
              disabled={disabled}
              style={{
                marginTop: 10, fontSize: '0.72rem',
                color: 'var(--accent)', background: 'rgba(99,102,241,0.1)',
                border: '1px solid rgba(99,102,241,0.25)', borderRadius: 7,
                padding: '5px 14px', cursor: disabled ? 'not-allowed' : 'pointer',
              }}
            >
              Browse file
            </button>
          </div>
        )}

        <input
          id="keyword-file-input"
          ref={fileInputRef}
          type="file"
          accept=".txt"
          style={{ display: 'none' }}
          onChange={onFileChange}
        />
      </div>
    </div>
  )
}
