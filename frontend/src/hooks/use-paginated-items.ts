import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { useAuth } from '@/hooks/use-auth'
import { ApiError } from '@/lib/api'
import type { ContentItem, PaginatedItems } from '@/lib/types'

type FetchPageParams = {
  limit: number
  offset: number
}

type UsePaginatedItemsOptions = {
  fetchPage: (params: FetchPageParams) => Promise<PaginatedItems>
  sortItems?: (items: ContentItem[]) => ContentItem[]
  resetKey?: string | number
}

export function usePaginatedItems({
  fetchPage,
  sortItems,
  resetKey,
}: UsePaginatedItemsOptions) {
  const { logout } = useAuth()
  const navigate = useNavigate()
  const [items, setItems] = useState<ContentItem[] | null>(null)
  const [total, setTotal] = useState(0)
  const [offset, setOffset] = useState(0)
  const [isLoadingMore, setIsLoadingMore] = useState(false)
  const [error, setError] = useState<string | null>(null)

  function applySort(nextItems: ContentItem[]): ContentItem[] {
    if (!sortItems) {
      return nextItems
    }
    return sortItems(nextItems)
  }

  function handleAuthError(caught: unknown): boolean {
    if (caught instanceof ApiError && caught.status === 401) {
      logout()
      navigate('/login', { replace: true })
      return true
    }
    return false
  }

  useEffect(() => {
    let cancelled = false

    fetchPage({ limit: 50, offset: 0 })
      .then((response) => {
        if (cancelled) {
          return
        }
        setItems(applySort(response.items))
        setTotal(response.total)
        setOffset(response.items.length)
        setError(null)
      })
      .catch((caught: unknown) => {
        if (cancelled) {
          return
        }
        if (handleAuthError(caught)) {
          return
        }
        setError(
          caught instanceof ApiError
            ? caught.message
            : 'Failed to load content.',
        )
        setItems([])
      })

    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [resetKey])

  function loadMore() {
    setIsLoadingMore(true)
    setError(null)

    fetchPage({ limit: 50, offset })
      .then((response) => {
        setItems((current) =>
          applySort([...(current ?? []), ...response.items]),
        )
        setTotal(response.total)
        setOffset((current) => current + response.items.length)
      })
      .catch((caught: unknown) => {
        if (handleAuthError(caught)) {
          return
        }
        setError(
          caught instanceof ApiError
            ? caught.message
            : 'Failed to load more content.',
        )
      })
      .finally(() => {
        setIsLoadingMore(false)
      })
  }

  function removeItem(itemId: string) {
    setItems((current) => {
      if (!current) {
        return current
      }
      return current.filter((item) => item.id !== itemId)
    })
    setTotal((current) => Math.max(0, current - 1))
  }

  const isLoading = items === null
  const hasMore = (items?.length ?? 0) < total

  return {
    items,
    total,
    isLoading,
    isLoadingMore,
    hasMore,
    error,
    loadMore,
    removeItem,
  }
}
