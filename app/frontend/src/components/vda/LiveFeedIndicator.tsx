import { useLiveFeed } from '@/hooks/useLiveFeed'

interface LiveFeedIndicatorProps {
  showControls?: boolean
  showStats?: boolean
  pollInterval?: number
}

export function LiveFeedIndicator({
  showControls = false,
  showStats = false,
  pollInterval = 15000,
}: LiveFeedIndicatorProps) {
  const { status, loading, start, stop } = useLiveFeed(pollInterval)

  const isRunning = status?.running ?? false

  return (
    <div className="flex items-center gap-3">
      {/* Status indicator */}
      <div className="flex items-center gap-1.5">
        {isRunning ? (
          <span className="h-2 w-2 rounded-full bg-success animate-pulse" />
        ) : (
          <span className="h-2 w-2 rounded-full bg-content-muted opacity-40" />
        )}
        <span className="text-content-muted text-xs">
          {loading && !status ? 'Loading...' : isRunning ? 'Live' : 'Offline'}
        </span>
      </div>

      {/* Controls */}
      {showControls && (
        <button
          onClick={isRunning ? stop : start}
          disabled={loading}
          className="text-xs text-content-muted hover:text-content-primary transition-colors disabled:opacity-50"
        >
          {isRunning ? 'Stop' : 'Start'}
        </button>
      )}

      {/* Stats */}
      {showStats && status && (
        <div className="flex items-center gap-3">
          {status.elapsed_seconds > 0 && (
            <span className="text-content-muted text-xs">
              {Math.floor(status.elapsed_seconds)}s elapsed
            </span>
          )}
          {Object.entries(status.stats).map(([stream, stat]) => (
            <span key={stream} className="text-content-muted text-xs">
              {stream}: {stat.rows_inserted} rows
              {stat.errors > 0 && (
                <span className="text-error ml-1">({stat.errors} err)</span>
              )}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
