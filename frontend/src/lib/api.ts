import axios from 'axios'
import { type SearchJob, type Lead, type LeadListResponse } from './types'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const getJobs = async (): Promise<{ jobs: SearchJob[]; total: number }> => {
  const res = await axios.get(`${API}/api/jobs`)
  return res.data
}

export const getJob = async (id: string): Promise<SearchJob> => {
  const res = await axios.get(`${API}/api/search/${id}`)
  return res.data
}

export const getLeads = async (
  jobId: string,
  page = 1,
  pageSize = 300,
  tag?: string
): Promise<LeadListResponse> => {
  const res = await axios.get(`${API}/api/search/${jobId}/leads`, {
    params: { page, page_size: pageSize, tag: tag && tag !== 'all' ? tag : undefined },
  })
  return res.data
}

export const deleteJob = async (id: string): Promise<void> => {
  await axios.delete(`${API}/api/search/${id}`)
}

export const getExportUrl = (jobId: string, tag?: string): string => {
  const tagParam = tag && tag !== 'all' ? `?tag=${tag}` : ''
  return `${API}/api/search/${jobId}/export${tagParam}`
}

export const getCategories = async (): Promise<string[]> => {
  const res = await axios.get(`${API}/api/categories`)
  return res.data
}

export const getCities = async (): Promise<string[]> => {
  const res = await axios.get(`${API}/api/cities`)
  return res.data
}

export const getCityLocalities = async (city: string) => {
  const res = await axios.get(`${API}/api/cities/${city}/localities`)
  return res.data
}
