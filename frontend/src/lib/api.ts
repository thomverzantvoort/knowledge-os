import { apiBaseUrl } from '@/lib/env'
import type {
  ContentItem,
  ContentItemDetail,
  PaginatedItems,
  TimeWindow,
  TokenResponse,
  UserStatus,
} from '@/lib/types'

const TOKEN_STORAGE_KEY = 'knowledge_os_token'

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

export function getStoredToken(): string | null {
  return sessionStorage.getItem(TOKEN_STORAGE_KEY)
}

export function setStoredToken(token: string): void {
  sessionStorage.setItem(TOKEN_STORAGE_KEY, token)
}

export function clearStoredToken(): void {
  sessionStorage.removeItem(TOKEN_STORAGE_KEY)
}

async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
  token?: string | null,
): Promise<T> {
  const authToken = token ?? getStoredToken()
  const headers = new Headers(options.headers)

  if (!headers.has('Content-Type') && options.body) {
    headers.set('Content-Type', 'application/json')
  }

  if (authToken) {
    headers.set('Authorization', `Bearer ${authToken}`)
  }

  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...options,
    headers,
  })

  if (!response.ok) {
    let detail = response.statusText
    try {
      const body = (await response.json()) as { detail?: string }
      if (body.detail) {
        detail = body.detail
      }
    } catch {
      // response body was not JSON
    }
    throw new ApiError(detail, response.status)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return (await response.json()) as T
}

export async function login(
  username: string,
  password: string,
): Promise<TokenResponse> {
  return apiFetch<TokenResponse>(
    '/auth/login',
    {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    },
    null,
  )
}

export type FetchItemsParams = {
  status?: 'all' | UserStatus
  windowHours?: number
  allTime?: boolean
  limit: number
  offset: number
}

export async function fetchItems(params: FetchItemsParams): Promise<PaginatedItems> {
  const search = new URLSearchParams({
    sort: 'chronological',
    status: params.status ?? 'all',
    limit: String(params.limit),
    offset: String(params.offset),
  })

  if (params.allTime) {
    search.set('all_time', 'true')
  } else if (params.windowHours !== undefined) {
    search.set('window_hours', String(params.windowHours))
  }

  return apiFetch<PaginatedItems>(`/items?${search.toString()}`)
}

export async function fetchInboxItems(params: {
  limit: number
  offset: number
}): Promise<PaginatedItems> {
  return fetchItems({
    status: 'unread',
    allTime: true,
    limit: params.limit,
    offset: params.offset,
  })
}

export async function fetchLibraryItems(params: {
  limit: number
  offset: number
}): Promise<PaginatedItems> {
  return fetchItems({
    status: 'interested',
    allTime: true,
    limit: params.limit,
    offset: params.offset,
  })
}

export async function fetchHistoryItems(params: {
  window: TimeWindow
  limit: number
  offset: number
}): Promise<PaginatedItems> {
  if (params.window === 'all') {
    return fetchItems({
      status: 'all',
      allTime: true,
      limit: params.limit,
      offset: params.offset,
    })
  }

  return fetchItems({
    status: 'all',
    windowHours: Number(params.window),
    limit: params.limit,
    offset: params.offset,
  })
}

export async function fetchItem(id: string): Promise<ContentItemDetail> {
  return apiFetch<ContentItemDetail>(`/items/${id}`)
}

export async function updateItemStatus(
  id: string,
  status: UserStatus,
): Promise<ContentItem> {
  return apiFetch<ContentItem>(`/items/${id}/status`, {
    method: 'PATCH',
    body: JSON.stringify({ status }),
  })
}
