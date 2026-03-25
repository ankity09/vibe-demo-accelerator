import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { api } from '@/lib/api'

interface UseApiOptions {
  autoFetch?: boolean
  params?: Record<string, string>
  pollInterval?: number
}

interface UseApiResult<T> {
  data: T | null
  loading: boolean
  error: Error | null
  refetch: () => Promise<void>
}

export function useApi<T = unknown>(
  endpoint: string,
  options: UseApiOptions = {}
): UseApiResult<T> {
  const { autoFetch = true, params, pollInterval } = options
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(autoFetch)
  const [error, setError] = useState<Error | null>(null)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const mountedRef = useRef(true)

  // Memoize params by their serialized form to avoid identity-change loops
  const stableParams = useMemo(
    () => params,
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [JSON.stringify(params)]
  )

  const refetch = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.get<T>(endpoint, { params: stableParams })
      if (mountedRef.current) setData(response.data)
    } catch (err) {
      const apiError = err instanceof Error ? err : new Error(String(err))
      if (mountedRef.current) setError(apiError)
      console.error(`useApi error for ${endpoint}:`, apiError)
    } finally {
      if (mountedRef.current) setLoading(false)
    }
  }, [endpoint, stableParams])

  // Cleanup on unmount — prevent setState on unmounted component
  useEffect(() => {
    mountedRef.current = true
    return () => {
      mountedRef.current = false
    }
  }, [])

  useEffect(() => {
    if (autoFetch) {
      refetch()
    }
  }, [autoFetch, refetch])

  useEffect(() => {
    if (pollInterval && pollInterval > 0) {
      intervalRef.current = setInterval(refetch, pollInterval)
      return () => {
        if (intervalRef.current) clearInterval(intervalRef.current)
      }
    }
  }, [pollInterval, refetch])

  return { data, loading, error, refetch }
}
