import { useState } from 'react'
import { useApi } from '@/hooks/useApi'
import { api } from '@/lib/api'
import { cn, timeAgo } from '@/lib/utils'

interface Exception {
  id: string
  title: string
  description?: string
  severity: string
  entity?: string
  timestamp: string | Date
  status?: string
}

type ExceptionAction = 'acknowledge' | 'escalate' | 'resolve' | 'dismiss'

interface ExceptionManagerProps {
  endpoint?: string
  severityColors?: Record<string, string>
  actions?: ExceptionAction[]
  onAskAI?: (prompt: string) => void
}

const defaultSeverityColors: Record<string, string> = {
  critical: 'red',
  high: 'amber',
  medium: 'blue',
  low: 'green',
}

const severityBadgeClass: Record<string, string> = {
  red: 'bg-error/10 text-error border-error/20',
  amber: 'bg-warning/10 text-warning border-warning/20',
  blue: 'bg-info/10 text-info border-info/20',
  green: 'bg-success/10 text-success border-success/20',
}

const actionButtonClass: Record<ExceptionAction, string> = {
  acknowledge: 'bg-info/10 text-info hover:bg-info/20',
  escalate: 'bg-warning/10 text-warning hover:bg-warning/20',
  resolve: 'bg-success/10 text-success hover:bg-success/20',
  dismiss: 'bg-surface-hover text-content-muted hover:bg-border',
}

const actionLabel: Record<ExceptionAction, string> = {
  acknowledge: 'Acknowledge',
  escalate: 'Escalate',
  resolve: 'Resolve',
  dismiss: 'Dismiss',
}

function SkeletonCard() {
  return (
    <div className="animate-pulse bg-surface-card border border-border rounded-lg p-4 mb-3">
      <div className="flex items-start gap-3 mb-3">
        <div className="h-5 w-16 bg-surface-hover rounded-full" />
        <div className="flex-1 h-5 bg-surface-hover rounded" />
      </div>
      <div className="h-4 bg-surface-hover rounded w-3/4 mb-2" />
      <div className="h-4 bg-surface-hover rounded w-1/2" />
    </div>
  )
}

export function ExceptionManager({
  endpoint = '/api/exceptions',
  severityColors = defaultSeverityColors,
  actions = ['acknowledge', 'escalate', 'resolve', 'dismiss'],
  onAskAI,
}: ExceptionManagerProps) {
  const { data, loading, refetch } = useApi<Exception[]>(endpoint)
  const [actioningId, setActioningId] = useState<string | null>(null)

  async function handleAction(exception: Exception, action: ExceptionAction) {
    setActioningId(exception.id)
    try {
      await api.patch(`${endpoint}/${exception.id}`, { status: action })
      await refetch()
    } catch (err) {
      console.error(`ExceptionManager: failed to ${action} exception ${exception.id}`, err)
    } finally {
      setActioningId(null)
    }
  }

  function handleAskAI(exception: Exception) {
    if (onAskAI) {
      onAskAI(`Tell me about exception: ${exception.title} - ${exception.description ?? ''}`)
    }
  }

  function getSeverityColor(severity: string): string {
    const colorKey = (severityColors[severity.toLowerCase()] ?? severity).toLowerCase()
    return colorKey
  }

  if (loading) {
    return (
      <div>
        {Array.from({ length: 3 }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    )
  }

  const exceptions = data ?? []

  if (exceptions.length === 0) {
    return (
      <div className="text-center py-12 text-content-muted text-sm">
        No exceptions to display.
      </div>
    )
  }

  return (
    <div>
      {exceptions.map((exception) => {
        const colorKey = getSeverityColor(exception.severity)
        const badgeClass = severityBadgeClass[colorKey] ?? 'bg-surface-hover text-content-muted border-border'
        const isActioning = actioningId === exception.id

        return (
          <div
            key={exception.id}
            className="bg-surface-card border border-border rounded-lg p-4 mb-3 transition-colors"
          >
            {/* Header row */}
            <div className="flex items-start gap-3 mb-2">
              <span
                className={cn(
                  'inline-flex items-center text-xs font-medium px-2 py-0.5 rounded-full border shrink-0 capitalize',
                  badgeClass
                )}
              >
                {exception.severity}
              </span>
              <span className="text-content-primary font-medium text-sm leading-snug flex-1">
                {exception.title}
              </span>
              <span className="text-content-muted text-xs shrink-0 mt-0.5">
                {timeAgo(exception.timestamp)}
              </span>
            </div>

            {/* Description */}
            {exception.description && (
              <p className="text-content-secondary text-sm leading-relaxed mb-2 pl-0">
                {exception.description}
              </p>
            )}

            {/* Entity reference */}
            {exception.entity && (
              <p className="text-content-muted text-xs mb-3 font-mono">
                {exception.entity}
              </p>
            )}

            {/* Action bar */}
            <div className="flex items-center gap-2 flex-wrap pt-2 border-t border-border">
              {actions.map((action) => (
                <button
                  key={action}
                  disabled={isActioning}
                  onClick={() => handleAction(exception, action)}
                  className={cn(
                    'text-xs px-2 py-1 rounded font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed',
                    actionButtonClass[action]
                  )}
                >
                  {actionLabel[action]}
                </button>
              ))}

              {onAskAI && (
                <button
                  onClick={() => handleAskAI(exception)}
                  className="ml-auto text-xs px-2 py-1 rounded font-medium bg-accent/10 text-accent hover:bg-accent/20 transition-colors"
                >
                  Ask AI
                </button>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}
