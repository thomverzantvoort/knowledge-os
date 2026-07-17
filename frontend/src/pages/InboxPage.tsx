import { useState } from 'react'
import { Loader2, RefreshCw } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

import { ContentCard } from '@/components/ContentCard'
import { ItemPreviewPanel } from '@/components/ItemPreviewPanel'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { usePaginatedItems } from '@/hooks/use-paginated-items'
import {
  ApiError,
  fetchInboxItems,
  syncSubscriptions,
  updateItemStatus,
} from '@/lib/api'
import type { ContentItem } from '@/lib/types'

function sortByRelevance(items: ContentItem[]): ContentItem[] {
  return [...items].sort((left, right) => {
    const leftScore = left.enrichment?.relevance_score ?? 0
    const rightScore = right.enrichment?.relevance_score ?? 0
    return rightScore - leftScore
  })
}

export function InboxPage() {
  const navigate = useNavigate()
  const [selectedItem, setSelectedItem] = useState<ContentItem | null>(null)
  const [previewOpen, setPreviewOpen] = useState(false)
  const [actionPending, setActionPending] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)
  const [refreshKey, setRefreshKey] = useState(0)
  const [syncPending, setSyncPending] = useState(false)
  const [syncError, setSyncError] = useState<string | null>(null)
  const [syncMessage, setSyncMessage] = useState<string | null>(null)

  const {
    items,
    total,
    isLoading,
    isLoadingMore,
    hasMore,
    error,
    loadMore,
    removeItem,
  } = usePaginatedItems({
    fetchPage: fetchInboxItems,
    sortItems: sortByRelevance,
    resetKey: refreshKey,
  })

  function handleSelect(item: ContentItem) {
    setActionError(null)
    setSelectedItem(item)
    setPreviewOpen(true)
  }

  function handlePreviewOpenChange(open: boolean) {
    setPreviewOpen(open)
    if (!open) {
      setSelectedItem(null)
      setActionError(null)
    }
  }

  async function handleRefresh() {
    setSyncPending(true)
    setSyncError(null)
    setSyncMessage(null)

    try {
      const result = await syncSubscriptions()
      const created = result.items_created
      setSyncMessage(
        created === 1 ? '1 new item' : `${created} new items`,
      )
      setRefreshKey((current) => current + 1)
    } catch (caught: unknown) {
      setSyncError(
        caught instanceof ApiError
          ? caught.message
          : 'Failed to refresh inbox.',
      )
    } finally {
      setSyncPending(false)
    }
  }

  async function handlePass() {
    if (!selectedItem) {
      return
    }

    setActionPending(true)
    setActionError(null)

    try {
      await updateItemStatus(selectedItem.id, 'dismissed')
      removeItem(selectedItem.id)
      setPreviewOpen(false)
      setSelectedItem(null)
    } catch (caught: unknown) {
      setActionError(
        caught instanceof ApiError ? caught.message : 'Failed to pass item.',
      )
    } finally {
      setActionPending(false)
    }
  }

  async function handleSave() {
    if (!selectedItem) {
      return
    }

    const itemId = selectedItem.id
    setActionPending(true)
    setActionError(null)

    try {
      await updateItemStatus(itemId, 'interested')
      removeItem(itemId)
      setPreviewOpen(false)
      setSelectedItem(null)
      navigate(`/library/${itemId}`)
    } catch (caught: unknown) {
      setActionError(
        caught instanceof ApiError ? caught.message : 'Failed to save item.',
      )
    } finally {
      setActionPending(false)
    }
  }

  return (
    <div className="flex h-full min-h-0 flex-col">
      <header className="shrink-0 border-b border-border">
        <div className="flex min-h-[5.5rem] flex-wrap items-center justify-between gap-4 px-6 py-4">
          <div className="flex flex-col gap-1">
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="font-heading text-xl font-medium">Inbox</h1>
              {!isLoading && total > 0 ? (
                <Badge variant="secondary">{total}</Badge>
              ) : null}
            </div>
            <p className="text-sm text-muted-foreground">
              Untriaged items waiting for Save or Pass
            </p>
            {syncError ? (
              <p className="text-sm text-destructive" role="alert">
                {syncError}
              </p>
            ) : null}
            {syncMessage && !syncError ? (
              <p className="text-sm text-muted-foreground">{syncMessage}</p>
            ) : null}
          </div>
          <Button
            variant="outline"
            disabled={syncPending}
            onClick={handleRefresh}
          >
            {syncPending ? (
              <Loader2 className="animate-spin" data-icon="inline-start" />
            ) : (
              <RefreshCw data-icon="inline-start" />
            )}
            {syncPending ? 'Refreshing...' : 'Refresh'}
          </Button>
        </div>
      </header>

      <main className="min-h-0 flex-1 overflow-y-auto px-6 py-6">
        <div className="mx-auto max-w-5xl">
          {error ? (
            <p className="text-sm text-destructive" role="alert">
              {error}
            </p>
          ) : null}

          {isLoading ? (
            <p className="text-sm text-muted-foreground">Loading inbox...</p>
          ) : null}

          {!isLoading && items && items.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              Inbox zero. Nothing left to triage.
            </p>
          ) : null}

          {!isLoading && items && items.length > 0 ? (
            <>
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                {items.map((item) => (
                  <ContentCard key={item.id} item={item} onSelect={handleSelect} />
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
          ) : null}
        </div>
      </main>

      <ItemPreviewPanel
        item={selectedItem}
        open={previewOpen}
        onOpenChange={handlePreviewOpenChange}
        mode="triage"
        onSave={handleSave}
        onPass={handlePass}
        actionPending={actionPending}
        actionError={actionError}
      />
    </div>
  )
}
