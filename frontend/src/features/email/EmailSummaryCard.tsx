import { clsx } from 'clsx'
import { getUrgencyColor, getSentimentIcon } from '@/utils/formatting'
import type { EmailSummary } from '@/types'

export const EmailSummaryCard = ({ summary }: { summary: EmailSummary }) => (
  <div className="card px-4 py-3 border-l-4 border-l-brand-500">
    <div className="flex items-center gap-2 flex-wrap">
      <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide mr-1">Summary</span>
      <span className="text-lg leading-none">{getSentimentIcon(summary.sentiment)}</span>
      <span className={clsx('px-2 py-0.5 rounded-full text-xs font-medium', getUrgencyColor(summary.urgency_level))}>
        {summary.urgency_level.charAt(0).toUpperCase() + summary.urgency_level.slice(1)} priority
      </span>
    </div>
    <p className="text-xs text-slate-600 leading-relaxed mt-2">{summary.summary_text}</p>
    {summary.key_points.length > 0 && (
      <div className="flex flex-wrap gap-x-4 mt-2">
        {summary.key_points.slice(0, 2).map((point, i) => (
          <span key={i} className="text-xs text-slate-500 before:content-['•'] before:mr-1 before:text-brand-400">
            {point}
          </span>
        ))}
      </div>
    )}
  </div>
)
