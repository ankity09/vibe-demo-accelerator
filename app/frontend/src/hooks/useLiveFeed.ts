import { useCallback } from 'react'
import { useApi } from './useApi'
import { api } from '@/lib/api'

interface LiveFeedStatus {
  running: boolean
  elapsed_seconds: number
  stats: Record<string, { rows_inserted: number; errors: number }>
}

export function useLiveFeed(pollInterval = 15000) {
  const { data, loading, error, refetch } = useApi<LiveFeedStatus>(
    '/api/streaming/live-feed-status',
    { pollInterval, autoFetch: true }
  )

  const start = useCallback(async () => {
    await api.post('/api/streaming/start-live-feed')
    refetch()
  }, [refetch])

  const stop = useCallback(async () => {
    await api.post('/api/streaming/stop-live-feed')
    refetch()
  }, [refetch])

  return { status: data, loading, error, start, stop, refetch }
}
