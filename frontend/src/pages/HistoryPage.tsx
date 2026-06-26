import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { ContentCard } from '@/components/ContentCard'
import { ItemPreviewPanel } from '@/components/ItemPreviewPanel'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useAuth } from '@/hooks/use-auth'
import { ApiError, fetchHistoryItems } from '@/lib/api'
import {
  TIME_WINDOW_LABELS,
  type ContentItem,
  type TimeWindow,
} from '@/lib/types'

const PAGE_SIZE = 50

type HistoryFeedProps = {
  window: TimeWindow
  onSelect: (item: ContentItem) => void
}

function HistoryFeed({ window, onSelect }: HistoryFeedProps) {
  const { logout } = useAuth()
  const navigate = useNavigate()
  const [items, setItems] = useState<ContentItem[] | null>(null)
  const [total, setTotal] = useState(0)
  const [offset, setOffset] = useState(0)
  const [isLoadingMore, setIsLoadingMore] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    fetchHistoryItems({ window, limit: PAGE_SIZE, offset: 0 })
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

    fetchHistoryItems({ window, limit: PAGE_SIZE, offset })
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
          <ContentCard key={item.id} item={item} onSelect={onSelect} />
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

export function HistoryPage() {
  const [window, setWindow] = useState<TimeWindow>('all')
  const [selectedItem, setSelectedItem] = useState<ContentItem | null>(null)
  const [previewOpen, setPreviewOpen] = useState(false)

  function handleSelect(item: ContentItem) {
    setSelectedItem(item)
    setPreviewOpen(true)
  }

  function handlePreviewOpenChange(open: boolean) {
    setPreviewOpen(open)
    if (!open) {
      setSelectedItem(null)
    }
  }

  return (
    <div className="flex h-full min-h-0 flex-col">
      <header className="shrink-0 border-b border-border">
        <div className="flex min-h-[5.5rem] flex-wrap items-center justify-between gap-4 px-6 py-4">
          <div>
            <h1 className="font-heading text-xl font-medium">History</h1>
            <p className="text-sm text-muted-foreground">
              Everything you&apos;ve ingested
            </p>
          </div>
          <Select
            value={window}
            onValueChange={(value) => setWindow(value as TimeWindow)}
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {(Object.keys(TIME_WINDOW_LABELS) as TimeWindow[]).map((key) => (
                <SelectItem key={key} value={key}>
                  {TIME_WINDOW_LABELS[key]}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </header>

      <main className="min-h-0 flex-1 overflow-y-auto px-6 py-6">
        <div className="mx-auto max-w-5xl">
          <HistoryFeed key={window} window={window} onSelect={handleSelect} />
        </div>
      </main>

      <ItemPreviewPanel
        item={selectedItem}
        open={previewOpen}
        onOpenChange={handlePreviewOpenChange}
      />
    </div>
  )
}
