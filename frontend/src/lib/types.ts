// API types for LeadScout

export interface SearchJob {
  id: string
  keyword: string
  location: string
  status: 'pending' | 'scraping' | 'enriching' | 'verifying' | 'completed' | 'failed'
  total_results: number
  processed_results: number
  error_message?: string
  created_at: string
  updated_at: string
}

export interface Enrichment {
  id: string
  emails: string[]
  social_links: Record<string, string>
  linkedin_url?: string
  instagram_url?: string
  facebook_url?: string
  twitter_url?: string
  enriched_at: string
}

export interface Verification {
  id: string
  verified_email?: string
  quality_score?: 'hot' | 'warm' | 'cold'
  ai_reasoning?: string
  email_belongs_to_business?: boolean
  verified_at: string
}

export interface Lead {
  id: string
  search_job_id: string
  business_name: string
  address?: string
  phone?: string
  rating?: number
  review_count?: number
  website_url?: string
  google_maps_url?: string
  category?: string
  status: 'scraped' | 'enriching' | 'enriched' | 'verified'
  created_at: string
  enrichment?: Enrichment
  verification?: Verification
}

export interface LeadListResponse {
  leads: Lead[]
  total: number
  page: number
  page_size: number
}

export interface JobListResponse {
  jobs: SearchJob[]
  total: number
}

export type WSMessage =
  | { type: 'status'; status: string; total?: number; error?: string }
  | { type: 'lead_scraped'; lead: Lead; total: number }
  | { type: 'lead_enriched'; lead_id: string; emails: string[] }
  | { type: 'lead_verified'; lead_id: string; quality_score: string }
