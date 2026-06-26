import { apiBaseUrl } from '@/lib/env'
import type { PaginatedItems, TimeWindow, TokenResponse } from '@/lib/types'

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

export async function fetchHistoryItems(params: {
  window: TimeWindow
  limit: number
  offset: number
}): Promise<PaginatedItems> {
  const search = new URLSearchParams({
    sort: 'chronological',
    status: 'all',
    limit: String(params.limit),
    offset: String(params.offset),
  })

  if (params.window === 'all') {
    search.set('all_time', 'true')
  } else {
    search.set('window_hours', params.window)
  }

  return apiFetch<PaginatedItems>(`/items?${search.toString()}`)
}
