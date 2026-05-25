// TypeScript interfaces for LeadScout v2

export interface VerificationData {
  id: string
  verified_email?: string
  quality_score?: 'hot' | 'warm' | 'cold'
  ai_reasoning?: string
  email_belongs_to_business?: boolean
  verified_at?: string
}

export interface EnrichmentData {
  id: string
  emails?: string[]
  social_links?: Record<string, string>
  linkedin_url?: string
  instagram_url?: string
  facebook_url?: string
  twitter_url?: string
  enriched_at?: string
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
  locality?: string
  status: string
  // Health audit
  website_tag?: 'NO_SITE' | 'FIX_NEEDED' | 'GOOD_SITE'
  ssl_ok?: boolean
  load_time_ms?: number
  mobile_friendly?: boolean
  http_status?: number
  health_issues?: string[]
  created_at: string
  enrichment?: EnrichmentData
  verification?: VerificationData
}

export interface SearchJob {
  id: string
  keyword: string
  location: string
  localities?: string[]
  categories?: string[]
  lead_goal?: number
  status: 'pending' | 'scraping' | 'health_check' | 'enriching' | 'verifying' | 'completed' | 'failed'
  total_results: number
  processed_results: number
  error_message?: string
  created_at: string
  updated_at: string
}

export interface WSMessage {
  type: string
  status?: string
  lead?: Partial<Lead>
  lead_id?: string
  count?: number
  total?: number
  error?: string
  keyword?: string
  index?: number
  total_keywords?: number
  keywords?: string[]
  website_tag?: string
  emails?: string[]
  quality_score?: string
}

export interface LeadListResponse {
  leads: Lead[]
  total: number
  page: number
  page_size: number
  count_no_site: number
  count_fix_needed: number
  count_good_site: number
}
