import { useNavigate } from 'react-router-dom'

import { ContentCard } from '@/components/ContentCard'
import { Button } from '@/components/ui/button'
import { usePaginatedItems } from '@/hooks/use-paginated-items'
import { fetchLibraryItems } from '@/lib/api'
import type { ContentItem } from '@/lib/types'

export function LibraryPage() {
  const navigate = useNavigate()

  const {
    items,
    isLoading,
    isLoadingMore,
    hasMore,
    error,
    loadMore,
  } = usePaginatedItems({
    fetchPage: fetchLibraryItems,
  })

  function handleSelect(item: ContentItem) {
    navigate(`/library/${item.id}`)
  }

  return (
    <div className="flex h-full min-h-0 flex-col">
      <header className="shrink-0 border-b border-border">
        <div className="flex min-h-[5.5rem] flex-wrap items-center justify-between gap-4 px-6 py-4">
          <div>
            <h1 className="font-heading text-xl font-medium">Library</h1>
            <p className="text-sm text-muted-foreground">Saved items</p>
          </div>
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
            <p className="text-sm text-muted-foreground">Loading library...</p>
          ) : null}

          {!isLoading && items && items.length === 0 ? (
            <p className="text-sm text-muted-foreground">No saved items yet.</p>
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
    </div>
  )
}
