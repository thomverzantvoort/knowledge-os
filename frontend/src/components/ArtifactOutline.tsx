import type { ChapterSection } from '@/lib/types'
import { formatTimestamp, youtubeUrlAt } from '@/lib/youtube'

type ArtifactOutlineProps = {
  chapters: ChapterSection[]
  videoUrl: string
}

export function ArtifactOutline({ chapters, videoUrl }: ArtifactOutlineProps) {
  return (
    <ol className="flex flex-col gap-6">
      {chapters.map((chapter) => (
        <li key={`${chapter.start_seconds}-${chapter.title}`} className="flex flex-col gap-2">
          <div className="flex flex-wrap items-baseline gap-2">
            <a
              href={youtubeUrlAt(videoUrl, chapter.start_seconds)}
              target="_blank"
              rel="noreferrer"
              className="font-mono text-sm font-medium text-primary hover:underline"
            >
              {formatTimestamp(chapter.start_seconds)}
            </a>
            <h3 className="font-heading text-base font-medium">{chapter.title}</h3>
          </div>
          <p className="text-sm leading-relaxed text-muted-foreground">
            {chapter.narrative}
          </p>
        </li>
      ))}
    </ol>
  )
}
