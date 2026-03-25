import { useState } from 'react'
import type { TimelineEvent } from '@/types'
import { cn, timeAgo } from '@/lib/utils'

interface TimelineViewProps {
  events: TimelineEvent[]
  groupBy?: 'day' | 'hour'
  maxItems?: number
  onEventClick?: (event: TimelineEvent) => void
}

const severityDotClass: Record<NonNullable<TimelineEvent['severity']>, string> = {
  critical: 'bg-error',
  high: 'bg-warning',
  medium: 'bg-info',
  low: 'bg-success',
}

function formatGroupHeader(date: Date, groupBy: 'day' | 'hour'): string {
  if (groupBy === 'day') {
    return date.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })
  }
  return date.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', hour12: true })
}

function getGroupKey(date: Date, groupBy: 'day' | 'hour'): string {
  if (groupBy === 'day') {
    return date.toISOString().slice(0, 10)
  }
  return date.toISOString().slice(0, 13)
}

export function TimelineView({
  events,
  groupBy = 'day',
  maxItems,
  onEventClick,
}: TimelineViewProps) {
  const [showAll, setShowAll] = useState(false)

  const visibleEvents = maxItems && !showAll ? events.slice(0, maxItems) : events
  const hasMore = maxItems !== undefined && events.length > maxItems && !showAll

  // Group events by day or hour
  const groups: { key: string; label: string; items: TimelineEvent[] }[] = []
  const groupMap = new Map<string, TimelineEvent[]>()

  for (const event of visibleEvents) {
    const d = new Date(event.timestamp)
    const key = getGroupKey(d, groupBy)
    if (!groupMap.has(key)) {
      groupMap.set(key, [])
    }
    groupMap.get(key)!.push(event)
  }

  // Sort groups chronologically (newest first)
  const sortedKeys = Array.from(groupMap.keys()).sort((a, b) => b.localeCompare(a))
  for (const key of sortedKeys) {
    const items = groupMap.get(key)!
    const sampleDate = new Date(items[0].timestamp)
    groups.push({ key, label: formatGroupHeader(sampleDate, groupBy), items })
  }

  return (
    <div className="relative">
      {groups.map((group) => (
        <div key={group.key} className="mb-6">
          {/* Group header */}
          <div className="flex items-center gap-3 mb-3">
            <span className="text-xs font-medium text-content-muted uppercase tracking-wider whitespace-nowrap">
              {group.label}
            </span>
            <div className="flex-1 border-t border-border" />
          </div>

          {/* Events in this group */}
          <div className="relative pl-6">
            {/* Vertical line */}
            <div className="absolute left-[7px] top-0 bottom-0 w-[2px] bg-border" />

            {group.items.map((event) => {
              const dotColor = event.severity
                ? severityDotClass[event.severity]
                : 'bg-content-muted'

              return (
                <div
                  key={event.id}
                  className={cn(
                    'relative mb-4 last:mb-0',
                    onEventClick && 'cursor-pointer'
                  )}
                  onClick={() => onEventClick?.(event)}
                >
                  {/* Dot */}
                  <div
                    className={cn(
                      'absolute left-[-21px] top-[6px] w-[10px] h-[10px] rounded-full border-2 border-surface-primary z-10',
                      dotColor
                    )}
                  />

                  {/* Card */}
                  <div
                    className={cn(
                      'bg-surface-card border border-border rounded-lg p-3 transition-colors',
                      onEventClick && 'hover:border-border-hover hover:bg-surface-hover'
                    )}
                  >
                    <div className="flex items-start justify-between gap-2 mb-1">
                      <span className="text-content-primary font-medium text-sm leading-snug">
                        {event.title}
                      </span>
                      <span className="text-content-muted text-xs shrink-0 mt-0.5">
                        {timeAgo(event.timestamp)}
                      </span>
                    </div>

                    {event.description && (
                      <p className="text-content-secondary text-sm leading-relaxed mb-2">
                        {event.description}
                      </p>
                    )}

                    {event.type && (
                      <span className="inline-block text-xs px-2 py-0.5 rounded-full bg-surface-hover text-content-muted border border-border font-mono">
                        {event.type}
                      </span>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      ))}

      {hasMore && (
        <div className="pl-6 mt-2">
          <button
            onClick={() => setShowAll(true)}
            className="text-sm text-accent hover:text-accent-hover transition-colors font-medium"
          >
            Show {events.length - maxItems!} more events
          </button>
        </div>
      )}

      {events.length === 0 && (
        <div className="text-center py-12 text-content-muted text-sm">
          No events to display.
        </div>
      )}
    </div>
  )
}
