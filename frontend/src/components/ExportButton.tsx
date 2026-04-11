'use client'

import { Download, FileText } from 'lucide-react'
import { getExportUrl } from '@/lib/api'

interface Props {
  jobId: string
  totalLeads: number
  disabled?: boolean
}

export default function ExportButton({ jobId, totalLeads, disabled }: Props) {
  const handleExport = () => {
    const url = getExportUrl(jobId)
    const a = document.createElement('a')
    a.href = url
    a.download = `leadscout_export_${jobId.slice(0, 8)}.csv`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
  }

  return (
    <button
      id="export-csv-btn"
      onClick={handleExport}
      disabled={disabled || totalLeads === 0}
      className="btn-primary"
      style={{
        background: disabled || totalLeads === 0
          ? 'rgba(99,102,241,0.2)'
          : 'linear-gradient(135deg, #10b981, #059669)',
        display: 'flex',
        alignItems: 'center',
        gap: 8,
      }}
      title={`Export ${totalLeads} leads to CSV`}
    >
      <Download size={16} />
      Export CSV
      {totalLeads > 0 && (
        <span style={{
          background: 'rgba(255,255,255,0.2)',
          borderRadius: 999,
          padding: '1px 7px',
          fontSize: '0.72rem',
          fontWeight: 700,
        }}>
          {totalLeads}
        </span>
      )}
    </button>
  )
}
