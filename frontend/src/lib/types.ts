export type Enrichment = {
  blurb: string
  tags: string[]
  content_type: string
  domain_matches: string[]
  relevance_score: number
  input_kind: string
  enriched_at: string
}

export type UserStatus = 'unread' | 'interested' | 'dismissed'

export const USER_STATUS_LABELS: Record<UserStatus, string> = {
  unread: 'New',
  interested: 'Saved',
  dismissed: 'Passed',
}

export type ContentItem = {
  id: string
  subscription_id: string
  title: string
  description: string | null
  url: string
  thumbnail_url: string | null
  author: string | null
  published_at: string
  kind: string
  user_status: UserStatus
  enrichment: Enrichment | null
}

export type PaginatedItems = {
  items: ContentItem[]
  total: number
  limit: number
  offset: number
}

export type TokenResponse = {
  access_token: string
  token_type: string
}

export type TimeWindow = '168' | '720' | 'all'

export const TIME_WINDOW_LABELS: Record<TimeWindow, string> = {
  '168': 'Last 7 days',
  '720': 'Last 30 days',
  all: 'All time',
}
