import { useCallback, useEffect, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, ChevronDown, Check, Loader2, AlertCircle } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { useSSE } from '@/hooks/useSSE'
import { useChatStore } from '@/stores/chatStore'
import { ActionCard } from '@/components/vda/ActionCard'
import { cn } from '@/lib/utils'
import type { ActionCardConfig, ActionCardData } from '@/types'

interface AgentChatProps {
  endpoint?: string
  welcomeTitle?: string
  welcomeSubtitle?: string
  suggestedPrompts?: string[]
  agentNameMap?: Record<string, string>
  actionCardTables?: ActionCardConfig[]
  showReasoning?: boolean
  autoApproveMcp?: boolean
}

function formatAgentName(name: string, agentNameMap?: Record<string, string>): string {
  if (agentNameMap?.[name]) return agentNameMap[name]
  const shortName = name.includes('__') ? name.split('__').pop()! : name
  if (agentNameMap?.[shortName]) return agentNameMap[shortName]
  return shortName.replace(/[-_]/g, ' ')
}

interface ReasoningBlockProps {
  text: string
  isStreaming?: boolean
}

function ReasoningBlock({ text, isStreaming }: ReasoningBlockProps) {
  const [open, setOpen] = useState(false)

  return (
    <div className="mb-3 rounded-lg border border-border bg-surface-secondary overflow-hidden">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-2 w-full px-3 py-2 text-xs text-content-muted hover:text-content-secondary transition-colors"
      >
        <motion.span
          animate={{ rotate: open ? 180 : 0 }}
          transition={{ duration: 0.2 }}
        >
          <ChevronDown size={12} />
        </motion.span>
        <span className="font-medium">
          {isStreaming ? 'Thinking...' : 'Reasoning'}
        </span>
        {isStreaming && (
          <span className="ml-auto flex items-center gap-1">
            <span className="inline-block w-1 h-1 rounded-full bg-accent animate-pulse" />
            <span className="inline-block w-1 h-1 rounded-full bg-accent animate-pulse [animation-delay:0.2s]" />
            <span className="inline-block w-1 h-1 rounded-full bg-accent animate-pulse [animation-delay:0.4s]" />
          </span>
        )}
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-3 pb-3 text-content-muted text-sm font-mono whitespace-pre-wrap leading-relaxed border-t border-border pt-2">
              {text}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

interface ToolCallStepsProps {
  toolCalls: string[]
  agentNameMap?: Record<string, string>
  isStreaming?: boolean
}

function ToolCallSteps({ toolCalls, agentNameMap, isStreaming }: ToolCallStepsProps) {
  return (
    <div className="mb-3 space-y-1">
      {toolCalls.map((tool, idx) => {
        const isLast = idx === toolCalls.length - 1
        const inProgress = isStreaming && isLast
        return (
          <div key={`${tool}-${idx}`} className="flex items-center gap-2">
            <div className="flex-shrink-0 w-4 h-4 rounded-full border border-border flex items-center justify-center">
              {inProgress ? (
                <Loader2 size={10} className="text-accent animate-spin" />
              ) : (
                <Check size={10} className="text-success" />
              )}
            </div>
            <span className="text-xs text-content-muted capitalize">
              {formatAgentName(tool, agentNameMap)}
            </span>
          </div>
        )
      })}
    </div>
  )
}

interface MarkdownContentProps {
  content: string
}

function MarkdownContent({ content }: MarkdownContentProps) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        p: ({ children }) => (
          <p className="text-content-primary text-sm leading-relaxed mb-2 last:mb-0">
            {children}
          </p>
        ),
        h1: ({ children }) => (
          <h1 className="text-content-primary font-display font-bold text-xl mb-3 mt-4 first:mt-0">
            {children}
          </h1>
        ),
        h2: ({ children }) => (
          <h2 className="text-content-primary font-semibold text-lg mb-2 mt-3 first:mt-0">
            {children}
          </h2>
        ),
        h3: ({ children }) => (
          <h3 className="text-content-primary font-semibold text-base mb-2 mt-3 first:mt-0">
            {children}
          </h3>
        ),
        ul: ({ children }) => (
          <ul className="list-disc list-inside text-content-primary text-sm mb-2 space-y-1 pl-2">
            {children}
          </ul>
        ),
        ol: ({ children }) => (
          <ol className="list-decimal list-inside text-content-primary text-sm mb-2 space-y-1 pl-2">
            {children}
          </ol>
        ),
        li: ({ children }) => (
          <li className="text-content-primary text-sm leading-relaxed">
            {children}
          </li>
        ),
        code: ({ className, children, ...props }) => {
          const isBlock = className?.includes('language-')
          if (isBlock) {
            return (
              <code
                className="block bg-surface-secondary rounded-lg p-3 font-mono text-sm text-content-primary overflow-x-auto"
                {...props}
              >
                {children}
              </code>
            )
          }
          return (
            <code
              className="bg-surface-hover rounded px-1 font-mono text-sm text-accent"
              {...props}
            >
              {children}
            </code>
          )
        },
        pre: ({ children }) => (
          <pre className="mb-3 overflow-x-auto">{children}</pre>
        ),
        a: ({ href, children }) => (
          <a
            href={href}
            target="_blank"
            rel="noopener noreferrer"
            className="text-accent hover:underline"
          >
            {children}
          </a>
        ),
        blockquote: ({ children }) => (
          <blockquote className="border-l-2 border-accent pl-3 text-content-secondary text-sm italic mb-2">
            {children}
          </blockquote>
        ),
        table: ({ children }) => (
          <div className="overflow-x-auto mb-3">
            <table className="w-full text-sm border-collapse border border-border rounded-lg overflow-hidden">
              {children}
            </table>
          </div>
        ),
        thead: ({ children }) => (
          <thead className="bg-surface-secondary text-content-secondary text-xs uppercase tracking-wider">
            {children}
          </thead>
        ),
        th: ({ children }) => (
          <th className="px-3 py-2 text-left border-b border-border font-semibold">
            {children}
          </th>
        ),
        td: ({ children }) => (
          <td className="px-3 py-2 border-b border-border text-content-primary">
            {children}
          </td>
        ),
        hr: () => <hr className="border-border my-3" />,
        strong: ({ children }) => (
          <strong className="text-content-primary font-semibold">{children}</strong>
        ),
        em: ({ children }) => (
          <em className="text-content-secondary italic">{children}</em>
        ),
      }}
    >
      {content}
    </ReactMarkdown>
  )
}

export function AgentChat({
  endpoint = '/api/chat',
  welcomeTitle = 'Welcome to AI Chat',
  welcomeSubtitle = 'Ask me anything about your data',
  suggestedPrompts = [],
  agentNameMap,
  showReasoning = true,
  autoApproveMcp = true,
}: AgentChatProps) {
  const {
    messages,
    isStreaming,
    currentThinking,
    currentResponse,
    currentToolCalls,
    currentActionCards,
    currentSuggestedActions,
    addMessage,
    setStreaming,
    appendThinking,
    appendResponse,
    addToolCall,
    addActionCard,
    setSuggestedActions,
    finishResponse,
  } = useChatStore()

  const [inputValue, setInputValue] = useState('')
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [sessionExpired, setSessionExpired] = useState(false)

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const scrollContainerRef = useRef<HTMLDivElement>(null)

  const { send, abort } = useSSE(endpoint, {
    onThinking: appendThinking,
    onDelta: appendResponse,
    onToolCall: addToolCall,
    onAgentSwitch: addToolCall,
    onSubResult: () => {},
    onActionCard: addActionCard,
    onSuggestedActions: setSuggestedActions,
    onDone: finishResponse,
    onError: (msg) => {
      setErrorMessage(msg)
      setStreaming(false)
    },
    onSessionExpired: () => {
      setSessionExpired(true)
      setStreaming(false)
    },
  })

  // Abort any in-flight stream when the component unmounts
  useEffect(() => {
    return () => abort()
  }, [abort])

  // Auto-scroll to bottom during streaming
  useEffect(() => {
    if (isStreaming || messages.length > 0) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages, isStreaming, currentResponse, currentThinking, currentToolCalls])

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`
    }
  }, [inputValue])

  const handleSend = useCallback(
    async (text?: string) => {
      const message = (text ?? inputValue).trim()
      if (!message || isStreaming) return

      setErrorMessage(null)
      setInputValue('')

      // Add user message to store
      addMessage({
        id: crypto.randomUUID(),
        role: 'user',
        content: message,
        timestamp: new Date(),
      })

      setStreaming(true)

      // Build history for API (exclude last user message we just added)
      const history = messages.map((m) => ({
        role: m.role,
        content: m.content,
      }))

      await send({
        message,
        history,
        auto_approve_mcp: autoApproveMcp,
      })
    },
    [inputValue, isStreaming, messages, addMessage, setStreaming, send, autoApproveMcp]
  )

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleActionCardAction = useCallback(
    async (action: string, id: string) => {
      // Map action to API call — patch the entity status
      try {
        await fetch(`/api/workflows/${id}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ status: action === 'approve' ? 'approved' : 'dismissed' }),
        })
      } catch {
        // silently ignore — demo mode
      }
    },
    []
  )

  const hasMessages = messages.length > 0
  const showStreamingMessage =
    isStreaming &&
    (currentThinking || currentResponse || currentToolCalls.length > 0)

  return (
    <div className="flex flex-col h-full bg-surface-primary">
      {/* Session expired banner */}
      <AnimatePresence>
        {sessionExpired && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="bg-error/10 border-b border-error/30 px-4 py-3 flex items-center gap-3"
          >
            <AlertCircle size={16} className="text-error flex-shrink-0" />
            <span className="text-sm text-error flex-1">
              Your session has expired. Please refresh the page to continue.
            </span>
            <button
              onClick={() => window.location.reload()}
              className="text-xs bg-error text-white px-3 py-1 rounded-md hover:bg-error/80 transition-colors"
            >
              Refresh
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Messages area */}
      <div
        ref={scrollContainerRef}
        className="flex-1 overflow-y-auto"
      >
        {!hasMessages && !isStreaming ? (
          /* Welcome state */
          <motion.div
            className="flex flex-col items-center justify-center h-full px-6 py-12 text-center"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
          >
            <h1 className="text-3xl font-display font-bold text-content-primary mb-3">
              {welcomeTitle}
            </h1>
            <p className="text-content-secondary mb-8 max-w-md">
              {welcomeSubtitle}
            </p>
            {suggestedPrompts.length > 0 && (
              <div className="flex flex-wrap gap-2 justify-center max-w-2xl">
                {suggestedPrompts.map((prompt, idx) => (
                  <motion.button
                    key={idx}
                    onClick={() => handleSend(prompt)}
                    className="bg-surface-card border border-border rounded-full px-4 py-2 hover:border-accent transition-colors text-sm text-content-secondary hover:text-content-primary"
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: idx * 0.05 + 0.2 }}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    {prompt}
                  </motion.button>
                ))}
              </div>
            )}
          </motion.div>
        ) : (
          /* Message list */
          <div className="px-4 py-6 space-y-6 max-w-4xl mx-auto w-full">
            <AnimatePresence initial={false}>
              {messages.map((msg) => (
                <motion.div
                  key={msg.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3 }}
                  className={cn(
                    'flex',
                    msg.role === 'user' ? 'justify-end' : 'justify-start'
                  )}
                >
                  {msg.role === 'user' ? (
                    <div className="bg-accent/10 text-content-primary rounded-2xl rounded-br-sm px-4 py-2 max-w-[80%] ml-auto text-sm leading-relaxed">
                      {msg.content}
                    </div>
                  ) : (
                    <div className="max-w-[85%] space-y-2">
                      {/* Reasoning block */}
                      {showReasoning && msg.thinking && (
                        <ReasoningBlock text={msg.thinking} />
                      )}

                      {/* Tool call steps */}
                      {msg.toolCalls && msg.toolCalls.length > 0 && (
                        <ToolCallSteps
                          toolCalls={msg.toolCalls}
                          agentNameMap={agentNameMap}
                          isStreaming={false}
                        />
                      )}

                      {/* Answer text */}
                      {msg.content && (
                        <div className="text-content-primary">
                          <MarkdownContent content={msg.content} />
                        </div>
                      )}

                      {/* Action cards */}
                      {msg.actionCards && msg.actionCards.length > 0 && (
                        <div className="space-y-2 mt-3">
                          {msg.actionCards.map((card: ActionCardData) => (
                            <ActionCard
                              key={card.id}
                              card={card}
                              onAction={handleActionCardAction}
                            />
                          ))}
                        </div>
                      )}

                      {/* Suggested follow-ups */}
                      {msg.suggestedActions && msg.suggestedActions.length > 0 && (
                        <div className="flex flex-wrap gap-2 mt-3">
                          {msg.suggestedActions.map((prompt, idx) => (
                            <button
                              key={idx}
                              onClick={() => handleSend(prompt)}
                              className="bg-surface-card border border-border rounded-full px-4 py-2 hover:border-accent transition-colors text-sm text-content-secondary hover:text-content-primary"
                            >
                              {prompt}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </motion.div>
              ))}

              {/* In-progress streaming message */}
              {showStreamingMessage && (
                <motion.div
                  key="streaming"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex justify-start"
                >
                  <div className="max-w-[85%] space-y-2">
                    {/* Live reasoning block */}
                    {showReasoning && currentThinking && (
                      <ReasoningBlock text={currentThinking} isStreaming />
                    )}

                    {/* Live tool call steps */}
                    {currentToolCalls.length > 0 && (
                      <ToolCallSteps
                        toolCalls={currentToolCalls}
                        agentNameMap={agentNameMap}
                        isStreaming
                      />
                    )}

                    {/* Live answer text */}
                    {currentResponse && (
                      <div className="text-content-primary">
                        <MarkdownContent content={currentResponse} />
                        {/* Pulsing cursor */}
                        <span className="inline-block w-2 h-4 bg-accent animate-pulse rounded-sm ml-0.5 align-text-bottom" />
                      </div>
                    )}

                    {/* Waiting indicator (no text yet) */}
                    {!currentResponse && !currentThinking && currentToolCalls.length === 0 && (
                      <div className="flex items-center gap-2 text-content-muted text-sm">
                        <Loader2 size={14} className="animate-spin text-accent" />
                        <span>Thinking...</span>
                      </div>
                    )}

                    {/* Live action cards */}
                    {currentActionCards.length > 0 && (
                      <div className="space-y-2 mt-3">
                        {currentActionCards.map((card: ActionCardData) => (
                          <ActionCard
                            key={card.id}
                            card={card}
                            onAction={handleActionCardAction}
                          />
                        ))}
                      </div>
                    )}

                    {/* Live suggested follow-ups */}
                    {currentSuggestedActions.length > 0 && (
                      <div className="flex flex-wrap gap-2 mt-3">
                        {currentSuggestedActions.map((prompt, idx) => (
                          <button
                            key={idx}
                            onClick={() => handleSend(prompt)}
                            disabled={isStreaming}
                            className="bg-surface-card border border-border rounded-full px-4 py-2 hover:border-accent transition-colors text-sm text-content-secondary hover:text-content-primary disabled:opacity-50"
                          >
                            {prompt}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                </motion.div>
              )}

              {/* Waiting for first byte */}
              {isStreaming && !showStreamingMessage && (
                <motion.div
                  key="waiting"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="flex justify-start"
                >
                  <div className="flex items-center gap-2 text-content-muted text-sm">
                    <Loader2 size={14} className="animate-spin text-accent" />
                    <span>Thinking...</span>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Error message */}
            <AnimatePresence>
              {errorMessage && (
                <motion.div
                  initial={{ opacity: 0, y: 5 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className="flex items-center gap-2 text-error text-sm p-3 bg-error/10 rounded-lg border border-error/20"
                >
                  <AlertCircle size={14} className="flex-shrink-0" />
                  <span>{errorMessage}</span>
                  <button
                    onClick={() => setErrorMessage(null)}
                    className="ml-auto text-error/60 hover:text-error transition-colors"
                  >
                    ×
                  </button>
                </motion.div>
              )}
            </AnimatePresence>

            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input area */}
      <div className="bg-surface-secondary border-t border-border p-4 flex-shrink-0">
        <div className="max-w-4xl mx-auto flex items-end gap-3">
          <textarea
            ref={textareaRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isStreaming || sessionExpired}
            placeholder={isStreaming ? 'AI is responding...' : 'Ask me anything...'}
            rows={1}
            className={cn(
              'flex-1 bg-surface-card border border-border rounded-xl px-4 py-3',
              'text-content-primary placeholder:text-content-muted text-sm',
              'resize-none overflow-hidden leading-relaxed',
              'focus:outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent',
              'transition-colors disabled:opacity-50 disabled:cursor-not-allowed'
            )}
          />
          <button
            onClick={() => handleSend()}
            disabled={!inputValue.trim() || isStreaming || sessionExpired}
            className={cn(
              'flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center',
              'bg-accent hover:bg-accent-hover text-white transition-colors',
              'disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-accent',
              'focus:outline-none focus:ring-2 focus:ring-accent/50'
            )}
            aria-label="Send message"
          >
            {isStreaming ? (
              <Loader2 size={16} className="animate-spin" />
            ) : (
              <Send size={16} />
            )}
          </button>
        </div>
        <p className="max-w-4xl mx-auto mt-2 text-xs text-content-muted">
          Enter to send · Shift+Enter for new line
        </p>
      </div>
    </div>
  )
}
