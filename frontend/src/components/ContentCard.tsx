import type { ContentItem } from '@/lib/types'
import { UserStatusBadge } from '@/components/UserStatusBadge'
import { Badge } from '@/components/ui/badge'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { cn } from '@/lib/utils'

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
    return item.description.length > 200
      ? `${item.description.slice(0, 200)}...`
      : item.description
  }
  return 'No summary available.'
}

type ContentCardProps = {
  item: ContentItem
  onSelect?: (item: ContentItem) => void
}

export function ContentCard({ item, onSelect }: ContentCardProps) {
  const tags = item.enrichment?.tags ?? []
  const isSelectable = Boolean(onSelect)

  return (
    <Card
      className={cn(
        'h-full overflow-hidden',
        isSelectable && 'cursor-pointer transition-colors hover:bg-muted/40',
      )}
      onClick={isSelectable ? () => onSelect?.(item) : undefined}
      onKeyDown={
        isSelectable
          ? (event) => {
              if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault()
                onSelect?.(item)
              }
            }
          : undefined
      }
      role={isSelectable ? 'button' : undefined}
      tabIndex={isSelectable ? 0 : undefined}
    >
      {item.thumbnail_url ? (
        isSelectable ? (
          <img
            src={item.thumbnail_url}
            alt=""
            className="aspect-video w-full object-cover"
          />
        ) : (
          <a href={item.url} target="_blank" rel="noreferrer">
            <img
              src={item.thumbnail_url}
              alt=""
              className="aspect-video w-full object-cover"
            />
          </a>
        )
      ) : null}
      <CardHeader>
        <div className="mb-2">
          <UserStatusBadge status={item.user_status} />
        </div>
        <CardTitle className="line-clamp-2 text-base leading-snug">
          {isSelectable ? (
            item.title
          ) : (
            <a
              href={item.url}
              target="_blank"
              rel="noreferrer"
              className="hover:underline"
            >
              {item.title}
            </a>
          )}
        </CardTitle>
        <CardDescription>
          {[item.author, formatPublishedAt(item.published_at)]
            .filter(Boolean)
            .join(' · ')}
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <p className="line-clamp-4 text-sm text-muted-foreground">
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
      </CardContent>
    </Card>
  )
}
