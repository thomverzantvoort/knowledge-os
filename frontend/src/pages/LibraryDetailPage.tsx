import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, Loader2, MessageSquare } from 'lucide-react'

import { ArtifactOutline } from '@/components/ArtifactOutline'
import { ArtifactSummaryView } from '@/components/ArtifactSummary'
import { Button } from '@/components/ui/button'
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs'
import { useAuth } from '@/hooks/use-auth'
import { ApiError, fetchItem } from '@/lib/api'
import type { ContentItemDetail } from '@/lib/types'

const POLL_INTERVAL_MS = 4000

function formatPublishedAt(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

export function LibraryDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { logout } = useAuth()
  const [trackedId, setTrackedId] = useState(id)
  const [item, setItem] = useState<ContentItemDetail | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  if (id !== trackedId) {
    setTrackedId(id)
    setItem(null)
    setError(null)
    setIsLoading(true)
  }

  useEffect(() => {
    if (!id) {
      return
    }

    const itemId = id
    let cancelled = false
    let pollTimer: ReturnType<typeof setInterval> | null = null

    function stopPolling() {
      if (pollTimer) {
        clearInterval(pollTimer)
        pollTimer = null
      }
    }

    async function loadItem() {
      try {
        const detail = await fetchItem(itemId)
        if (cancelled) {
          return
        }
        setItem(detail)
        setError(null)
        setIsLoading(false)

        const needsPoll =
          detail.artifact === null && detail.processing_status === 'ingested'
        if (needsPoll) {
          if (!pollTimer) {
            pollTimer = setInterval(() => {
              void loadItem()
            }, POLL_INTERVAL_MS)
          }
        } else {
          stopPolling()
        }
      } catch (caught: unknown) {
        if (cancelled) {
          return
        }
        stopPolling()
        if (caught instanceof ApiError && caught.status === 401) {
          logout()
          navigate('/login', { replace: true })
          return
        }
        setError(
          caught instanceof ApiError
            ? caught.message
            : 'Failed to load item.',
        )
        setIsLoading(false)
      }
    }

    void loadItem()

    return () => {
      cancelled = true
      stopPolling()
    }
  }, [id, logout, navigate])

  if (!id) {
    return (
      <div className="flex h-full items-center justify-center p-6">
        <p className="text-sm text-muted-foreground">Item not found.</p>
      </div>
    )
  }

  if (isLoading && !item) {
    return (
      <div className="flex h-full items-center justify-center p-6">
        <p className="text-sm text-muted-foreground">Loading...</p>
      </div>
    )
  }

  if (error && !item) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-4 p-6">
        <p className="text-sm text-destructive" role="alert">
          {error}
        </p>
        <Button variant="outline" asChild>
          <Link to="/library">Back to library</Link>
        </Button>
      </div>
    )
  }

  if (!item) {
    return null
  }

  const metaParts = [item.author, formatPublishedAt(item.published_at)].filter(
    Boolean,
  )
  const isProcessing =
    item.artifact === null && item.processing_status === 'ingested'
  const isFailed = item.processing_status === 'failed'

  return (
    <div className="flex h-full min-h-0 flex-col">
      <header className="shrink-0 border-b border-border">
        <div className="flex min-h-[5.5rem] flex-wrap items-center justify-between gap-4 px-6 py-4">
          <div className="flex min-w-0 flex-1 flex-col gap-2">
            <Button variant="ghost" size="sm" className="w-fit gap-2 px-0" asChild>
              <Link to="/library">
                <ArrowLeft className="size-4" />
                Back to library
              </Link>
            </Button>
            <h1 className="font-heading text-xl font-medium leading-snug">
              {item.title}
            </h1>
            {metaParts.length > 0 ? (
              <p className="text-sm text-muted-foreground">
                {metaParts.join(' · ')}
              </p>
            ) : null}
          </div>
          <Button variant="outline" disabled className="gap-2">
            <MessageSquare className="size-4" />
            Chat (coming soon)
          </Button>
        </div>
      </header>

      <main className="min-h-0 flex-1 overflow-y-auto px-6 py-6">
        <div className="mx-auto max-w-3xl">
          {item.thumbnail_url ? (
            <img
              src={item.thumbnail_url}
              alt=""
              className="mb-6 aspect-video w-full rounded-lg object-cover"
            />
          ) : null}

          {isFailed ? (
            <div className="flex flex-col items-center gap-4 py-12 text-center">
              <p className="text-sm text-destructive" role="alert">
                Deep processing failed. The outline and summary could not be
                generated.
              </p>
              <Button variant="outline" asChild>
                <Link to="/library">Back to library</Link>
              </Button>
            </div>
          ) : null}

          {isProcessing ? (
            <div className="flex flex-col items-center gap-3 py-12 text-center">
              <Loader2 className="size-6 animate-spin text-muted-foreground" />
              <p className="text-sm text-muted-foreground">
                Generating outline and summary...
              </p>
            </div>
          ) : null}

          {!isFailed && !isProcessing && item.artifact ? (
            <Tabs defaultValue="outline">
              <TabsList>
                <TabsTrigger value="outline">Outline</TabsTrigger>
                <TabsTrigger value="summary">Summary</TabsTrigger>
              </TabsList>
              <TabsContent value="outline" className="mt-6">
                <ArtifactOutline
                  chapters={item.artifact.chapters}
                  videoUrl={item.url}
                />
              </TabsContent>
              <TabsContent value="summary" className="mt-6">
                <ArtifactSummaryView summary={item.artifact.summary} />
              </TabsContent>
            </Tabs>
          ) : null}
        </div>
      </main>
    </div>
  )
}
