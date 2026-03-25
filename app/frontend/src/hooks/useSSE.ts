import { useCallback, useRef, useState } from 'react'
import type { ActionCardData, McpApprovalRequest } from '@/types'

interface UseSSEOptions {
  onThinking?: (text: string) => void
  onDelta?: (text: string) => void
  onToolCall?: (tool: string) => void
  onAgentSwitch?: (agent: string) => void
  onSubResult?: (data: unknown) => void
  onActionCard?: (card: ActionCardData) => void
  onSuggestedActions?: (actions: string[]) => void
  onMcpApproval?: (request: McpApprovalRequest) => void
  onError?: (message: string) => void
  onSessionExpired?: () => void
  onDone?: () => void
}

export function useSSE(endpoint: string, options: UseSSEOptions = {}) {
  const [isStreaming, setIsStreaming] = useState(false)
  const abortRef = useRef<AbortController | null>(null)
  // Store options in a ref so the send callback never goes stale
  // but also never causes re-creation of the callback.
  const optionsRef = useRef(options)
  optionsRef.current = options

  const send = useCallback(async (body: Record<string, unknown>) => {
    if (abortRef.current) abortRef.current.abort()
    const controller = new AbortController()
    abortRef.current = controller
    setIsStreaming(true)

    const opts = optionsRef.current

    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
        signal: controller.signal,
      })

      if (!response.ok) {
        opts.onError?.(`HTTP ${response.status}: ${response.statusText}`)
        return
      }

      if (!response.body) {
        opts.onError?.('Response body is null')
        return
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const data = line.slice(6).trim()
          if (data === '[DONE]') {
            optionsRef.current.onDone?.()
            setIsStreaming(false)
            return
          }
          if (!data) continue

          try {
            const parsed = JSON.parse(data)
            const event = parsed.event || parsed.type
            const o = optionsRef.current

            switch (event) {
              case 'thinking':
                o.onThinking?.(parsed.text || parsed.content || '')
                break
              case 'delta':
                o.onDelta?.(parsed.text || parsed.content || '')
                break
              case 'tool_call':
                o.onToolCall?.(parsed.name || parsed.tool || '')
                break
              case 'agent_switch':
                o.onAgentSwitch?.(parsed.name || parsed.agent || '')
                break
              case 'sub_result':
                o.onSubResult?.(parsed.data || parsed)
                break
              case 'action_card':
                o.onActionCard?.(parsed.card || parsed)
                break
              case 'suggested_actions':
                o.onSuggestedActions?.(parsed.actions || [])
                break
              case 'mcp_approval':
                o.onMcpApproval?.(parsed.request || parsed)
                break
              case 'error':
                o.onError?.(parsed.message || parsed.text || 'Unknown error')
                break
              case 'session_expired':
                o.onSessionExpired?.()
                break
              default:
                // Unknown event type — check for text content as fallback
                if (parsed.text || parsed.content) {
                  o.onDelta?.(parsed.text || parsed.content)
                }
            }
          } catch {
            // Non-JSON SSE data — treat as plain text delta
            optionsRef.current.onDelta?.(data)
          }
        }
      }
    } catch (err) {
      if ((err as Error).name !== 'AbortError') {
        optionsRef.current.onError?.((err as Error).message || 'Stream failed')
      }
    } finally {
      setIsStreaming(false)
      abortRef.current = null
    }
  }, [endpoint])

  const abort = useCallback(() => {
    abortRef.current?.abort()
    setIsStreaming(false)
  }, [])

  return { send, abort, isStreaming }
}
