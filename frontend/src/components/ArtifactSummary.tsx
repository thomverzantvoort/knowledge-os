import type { ArtifactSummary } from '@/lib/types'

type ArtifactSummaryViewProps = {
  summary: ArtifactSummary
}

const EFFORT_LABELS = {
  low: 'Low effort',
  medium: 'Medium effort',
  high: 'High effort',
} as const

export function ArtifactSummaryView({ summary }: ArtifactSummaryViewProps) {
  return (
    <div className="flex flex-col gap-8">
      <section className="flex flex-col gap-2">
        <h3 className="font-heading text-sm font-medium uppercase tracking-wide text-muted-foreground">
          Overview
        </h3>
        <p className="text-sm leading-relaxed">{summary.overview}</p>
      </section>

      <section className="flex flex-col gap-2">
        <h3 className="font-heading text-sm font-medium uppercase tracking-wide text-muted-foreground">
          Key takeaways
        </h3>
        <ul className="list-disc space-y-1 pl-5 text-sm leading-relaxed">
          {summary.key_takeaways.map((takeaway) => (
            <li key={takeaway}>{takeaway}</li>
          ))}
        </ul>
      </section>

      {summary.actionable.length > 0 ? (
        <section className="flex flex-col gap-3">
          <h3 className="font-heading text-sm font-medium uppercase tracking-wide text-muted-foreground">
            Actionable
          </h3>
          <ul className="flex flex-col gap-3">
            {summary.actionable.map((item) => (
              <li
                key={`${item.what}-${item.why}`}
                className="rounded-lg border border-border p-4"
              >
                <p className="text-sm font-medium">{item.what}</p>
                <p className="mt-1 text-sm text-muted-foreground">{item.why}</p>
                <p className="mt-2 text-xs text-muted-foreground">
                  {EFFORT_LABELS[item.effort]}
                </p>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {summary.learn_or_prioritize.length > 0 ? (
        <section className="flex flex-col gap-2">
          <h3 className="font-heading text-sm font-medium uppercase tracking-wide text-muted-foreground">
            Learn or prioritize
          </h3>
          <ul className="list-disc space-y-1 pl-5 text-sm leading-relaxed">
            {summary.learn_or_prioritize.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </section>
      ) : null}

      <section className="flex flex-col gap-2">
        <h3 className="font-heading text-sm font-medium uppercase tracking-wide text-muted-foreground">
          Skepticism
        </h3>
        <p className="text-sm leading-relaxed">{summary.skepticism}</p>
      </section>

      <section className="flex flex-col gap-2">
        <h3 className="font-heading text-sm font-medium uppercase tracking-wide text-muted-foreground">
          Worth watching
        </h3>
        <p className="text-sm leading-relaxed">{summary.worth_watching}</p>
      </section>
    </div>
  )
}
