import { useCallback } from 'react'
import { useApi } from './useApi'
import { api } from '@/lib/api'

interface LiveFeedStatus {
  running: boolean
  elapsed_seconds: number
  stats: Record<string, { rows_inserted: number; errors: number }>
}

export function useLiveFeed(pollInterval = 15000) {
  // Paths are relative to the axios baseURL (/api), so no /api prefix here
  const { data, loading, error, refetch } = useApi<LiveFeedStatus>(
    '/streaming/live-feed-status',
    { pollInterval, autoFetch: true }
  )

  const start = useCallback(async () => {
    await api.post('/streaming/start-live-feed')
    refetch()
  }, [refetch])

  const stop = useCallback(async () => {
    await api.post('/streaming/stop-live-feed')
    refetch()
  }, [refetch])

  return { status: data, loading, error, start, stop, refetch }
}
