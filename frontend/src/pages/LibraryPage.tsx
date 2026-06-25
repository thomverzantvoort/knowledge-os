import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { ContentCard } from '@/components/ContentCard'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useAuth } from '@/hooks/use-auth'
import { ApiError, fetchItems } from '@/lib/api'
import {
  TIME_WINDOW_LABELS,
  type ContentItem,
  type TimeWindow,
} from '@/lib/types'

const PAGE_SIZE = 50

type LibraryFeedProps = {
  window: TimeWindow
}

function LibraryFeed({ window }: LibraryFeedProps) {
  const { logout } = useAuth()
  const navigate = useNavigate()
  const [items, setItems] = useState<ContentItem[] | null>(null)
  const [total, setTotal] = useState(0)
  const [offset, setOffset] = useState(0)
  const [isLoadingMore, setIsLoadingMore] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    fetchItems({ window, limit: PAGE_SIZE, offset: 0 })
      .then((response) => {
        if (cancelled) {
          return
        }
        setItems(response.items)
        setTotal(response.total)
        setOffset(response.items.length)
        setError(null)
      })
      .catch((caught: unknown) => {
        if (cancelled) {
          return
        }
        if (caught instanceof ApiError && caught.status === 401) {
          logout()
          navigate('/login', { replace: true })
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
  }, [window, logout, navigate])

  function loadMore() {
    setIsLoadingMore(true)
    setError(null)

    fetchItems({ window, limit: PAGE_SIZE, offset })
      .then((response) => {
        setItems((current) => [...(current ?? []), ...response.items])
        setTotal(response.total)
        setOffset((current) => current + response.items.length)
      })
      .catch((caught: unknown) => {
        if (caught instanceof ApiError && caught.status === 401) {
          logout()
          navigate('/login', { replace: true })
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

  const isLoading = items === null
  const hasMore = (items?.length ?? 0) < total

  if (error) {
    return (
      <p className="text-sm text-destructive" role="alert">
        {error}
      </p>
    )
  }

  if (isLoading) {
    return <p className="text-sm text-muted-foreground">Loading content...</p>
  }

  if (items.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        No content in this time range.
      </p>
    )
  }

  return (
    <>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {items.map((item) => (
          <ContentCard key={item.id} item={item} />
        ))}
      </div>
      {hasMore ? (
        <div className="mt-6 flex justify-center">
          <Button
            variant="outline"
            disabled={isLoadingMore}
            onClick={loadMore}
          >
            {isLoadingMore ? 'Loading...' : 'Load more'}
          </Button>
        </div>
      ) : null}
    </>
  )
}

export function LibraryPage() {
  const { logout } = useAuth()
  const [window, setWindow] = useState<TimeWindow>('168')

  return (
    <div className="min-h-svh bg-background">
      <header className="border-b border-border">
        <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-4 px-6 py-4">
          <div>
            <h1 className="font-heading text-xl font-medium">Library</h1>
            <p className="text-sm text-muted-foreground">Your ingested content</p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <Select
              value={window}
              onValueChange={(value) => setWindow(value as TimeWindow)}
            >
              <SelectTrigger className="w-[180px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {(Object.keys(TIME_WINDOW_LABELS) as TimeWindow[]).map(
                  (key) => (
                    <SelectItem key={key} value={key}>
                      {TIME_WINDOW_LABELS[key]}
                    </SelectItem>
                  ),
                )}
              </SelectContent>
            </Select>
            <Button variant="outline" onClick={logout}>
              Sign out
            </Button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-6 py-6">
        <LibraryFeed key={window} window={window} />
      </main>
    </div>
  )
}
