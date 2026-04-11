// API client for LeadScout backend
import axios from 'axios'
import type { SearchJob, LeadListResponse, JobListResponse } from './types'

const BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const api = axios.create({ baseURL: BASE })

export async function createSearch(keyword: string, location: string, max_results = 30): Promise<SearchJob> {
  const { data } = await api.post('/api/search', { keyword, location, max_results })
  return data
}

export async function getJob(id: string): Promise<SearchJob> {
  const { data } = await api.get(`/api/search/${id}`)
  return data
}

export async function getLeads(jobId: string, page = 1, pageSize = 100): Promise<LeadListResponse> {
  const { data } = await api.get(`/api/search/${jobId}/leads`, {
    params: { page, page_size: pageSize },
  })
  return data
}

export async function getJobs(): Promise<JobListResponse> {
  const { data } = await api.get('/api/jobs')
  return data
}

export async function deleteJob(id: string): Promise<void> {
  await api.delete(`/api/search/${id}`)
}

export function getExportUrl(jobId: string): string {
  return `${BASE}/api/search/${jobId}/export`
}

export function createWebSocket(jobId: string): WebSocket {
  const wsBase = BASE.replace(/^http/, 'ws')
  return new WebSocket(`${wsBase}/api/ws/${jobId}`)
}
