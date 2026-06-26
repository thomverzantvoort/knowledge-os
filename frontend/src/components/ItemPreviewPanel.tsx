import type { ContentItem } from '@/lib/types'
import { UserStatusBadge } from '@/components/UserStatusBadge'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet'

function formatPublishedAt(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

function previewText(item: ContentItem): string {
  if (item.enrichment?.blurb) {
    return item.enrichment.blurb
  }
  if (item.description) {
    return item.description
  }
  return 'No summary available.'
}

function formatRelevanceScore(score: number): string {
  return `${Math.round(score * 100)}%`
}

type ItemPreviewPanelProps = {
  item: ContentItem | null
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function ItemPreviewPanel({
  item,
  open,
  onOpenChange,
}: ItemPreviewPanelProps) {
  if (!item) {
    return null
  }

  const tags = item.enrichment?.tags ?? []
  const metaParts = [
    item.author,
    formatPublishedAt(item.published_at),
    item.enrichment
      ? `Relevance ${formatRelevanceScore(item.enrichment.relevance_score)}`
      : null,
  ].filter(Boolean)

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-full overflow-y-auto sm:max-w-lg">
        <SheetHeader className="pr-10">
          <div className="flex flex-wrap items-center gap-2">
            <UserStatusBadge status={item.user_status} />
          </div>
          <SheetTitle className="text-left text-lg leading-snug">
            {item.title}
          </SheetTitle>
          {metaParts.length > 0 ? (
            <SheetDescription className="text-left">
              {metaParts.join(' · ')}
            </SheetDescription>
          ) : null}
        </SheetHeader>

        <div className="flex flex-col gap-4 px-6 pb-6">
          {item.thumbnail_url ? (
            <img
              src={item.thumbnail_url}
              alt=""
              className="aspect-video w-full rounded-lg object-cover"
            />
          ) : null}

          <p className="text-sm leading-relaxed text-foreground">
            {previewText(item)}
          </p>

          {tags.length > 0 ? (
            <div className="flex flex-wrap gap-1.5">
              {tags.map((tag) => (
                <Badge key={tag} variant="secondary">
                  {tag}
                </Badge>
              ))}
            </div>
          ) : null}
        </div>

        <SheetFooter>
          <Button variant="outline" asChild>
            <a href={item.url} target="_blank" rel="noreferrer">
              Open on YouTube
            </a>
          </Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  )
}
