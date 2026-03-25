import { useState } from 'react'
import { X, Search, Check, AlertTriangle, Clock, MessageSquare } from 'lucide-react'
import { useApi } from '@/hooks/useApi'
import { api } from '@/lib/api'
import { cn, timeAgo } from '@/lib/utils'

interface Workflow {
  id: string
  workflow_type: string
  severity: string
  summary: string
  reasoning?: unknown
  entity?: string
  created_at: string | Date
  updated_at?: string | Date
  status: string
}

interface AgentOverviewResponse {
  workflows?: Workflow[]
  [key: string]: unknown
}

interface WorkflowPanelProps {
  /** API endpoint path relative to axios baseURL (e.g. '/agent-overview', NOT '/api/agent-overview') */
  endpoint?: string
  workflowTypes?: string[]
  severityLevels?: string[]
  agentSteps?: Record<string, string[]>
  onAskAI?: (prompt: string) => void
}

const severityBadgeClass: Record<string, string> = {
  critical: 'bg-error/10 text-error border-error/20',
  high: 'bg-warning/10 text-warning border-warning/20',
  medium: 'bg-info/10 text-info border-info/20',
  low: 'bg-success/10 text-success border-success/20',
}

const statusBadgeClass: Record<string, string> = {
  pending_approval: 'bg-warning/10 text-warning border-warning/20',
  in_progress: 'bg-info/10 text-info border-info/20',
  completed: 'bg-success/10 text-success border-success/20',
  dismissed: 'bg-surface-hover text-content-muted border-border',
}

const STATUS_OPTIONS = [
  { value: 'all', label: 'All' },
  { value: 'pending_approval', label: 'Pending Approval' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'completed', label: 'Completed' },
]

const SEVERITY_OPTIONS = [
  { value: 'all', label: 'All' },
  { value: 'critical', label: 'Critical' },
  { value: 'high', label: 'High' },
  { value: 'medium', label: 'Medium' },
  { value: 'low', label: 'Low' },
]

function formatStatus(status: string): string {
  return status.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

function formatWorkflowType(type: string): string {
  return type.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

function SkeletonCard() {
  return (
    <div className="animate-pulse bg-surface-card border border-border rounded-lg p-4">
      <div className="flex items-start gap-2 mb-3">
        <div className="h-5 w-16 bg-surface-hover rounded-full" />
        <div className="h-5 w-20 bg-surface-hover rounded-full" />
      </div>
      <div className="h-4 bg-surface-hover rounded w-full mb-2" />
      <div className="h-4 bg-surface-hover rounded w-3/4 mb-3" />
      <div className="h-3 bg-surface-hover rounded w-1/3" />
    </div>
  )
}

interface AgentFlowDiagramProps {
  steps: string[]
  currentStatus: string
}

function AgentFlowDiagram({ steps, currentStatus }: AgentFlowDiagramProps) {
  const completedIndex =
    currentStatus === 'completed'
      ? steps.length
      : currentStatus === 'in_progress'
        ? Math.floor(steps.length / 2)
        : 1

  return (
    <div className="flex flex-col gap-0">
      {steps.map((step, idx) => {
        const isDone = idx < completedIndex
        const isActive = idx === completedIndex
        return (
          <div key={step} className="flex items-start gap-3">
            <div className="flex flex-col items-center">
              <div
                className={cn(
                  'w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold border-2 shrink-0',
                  isDone
                    ? 'bg-success border-success text-white'
                    : isActive
                      ? 'bg-accent border-accent text-white'
                      : 'bg-surface-hover border-border text-content-muted'
                )}
              >
                {isDone ? <Check size={13} /> : idx + 1}
              </div>
              {idx < steps.length - 1 && (
                <div
                  className={cn(
                    'w-0.5 h-6',
                    isDone ? 'bg-success' : 'bg-border'
                  )}
                />
              )}
            </div>
            <div className="pt-1 pb-1">
              <span
                className={cn(
                  'text-sm font-medium',
                  isDone
                    ? 'text-success'
                    : isActive
                      ? 'text-accent'
                      : 'text-content-muted'
                )}
              >
                {step}
              </span>
            </div>
          </div>
        )
      })}
    </div>
  )
}

interface WorkflowDetailModalProps {
  workflow: Workflow
  agentSteps?: Record<string, string[]>
  onClose: () => void
  onApprove: () => Promise<void>
  onDismiss: () => Promise<void>
  onAskAI?: (prompt: string) => void
  actioning: boolean
  workflowEndpoint: string
}

function WorkflowDetailModal({
  workflow,
  agentSteps,
  onClose,
  onApprove,
  onDismiss,
  onAskAI,
  actioning,
}: WorkflowDetailModalProps) {
  const [reasoningExpanded, setReasoningExpanded] = useState(false)
  const steps = agentSteps?.[workflow.workflow_type]
  const severityKey = workflow.severity?.toLowerCase() ?? 'medium'
  const badgeClass =
    severityBadgeClass[severityKey] ?? 'bg-surface-hover text-content-muted border-border'
  const statusKey = workflow.status?.toLowerCase() ?? ''
  const statusClass =
    statusBadgeClass[statusKey] ?? 'bg-surface-hover text-content-muted border-border'

  const reasoningStr =
    workflow.reasoning != null
      ? typeof workflow.reasoning === 'string'
        ? workflow.reasoning
        : JSON.stringify(workflow.reasoning, null, 2)
      : null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Overlay */}
      <div
        className="absolute inset-0 bg-black/50"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Panel */}
      <div className="bg-surface-card border border-border rounded-xl w-full max-w-3xl max-h-[80vh] overflow-y-auto p-6 relative z-10 mx-4">
        {/* Header */}
        <div className="flex items-start justify-between mb-5">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-content-primary font-semibold text-lg">
              {formatWorkflowType(workflow.workflow_type)}
            </span>
            <span
              className={cn(
                'inline-flex items-center text-xs font-medium px-2 py-0.5 rounded-full border capitalize',
                badgeClass
              )}
            >
              {workflow.severity}
            </span>
            <span
              className={cn(
                'inline-flex items-center text-xs font-medium px-2 py-0.5 rounded-full border capitalize',
                statusClass
              )}
            >
              {formatStatus(workflow.status)}
            </span>
          </div>
          <button
            onClick={onClose}
            className="text-content-muted hover:text-content-primary transition-colors ml-2 shrink-0"
            aria-label="Close modal"
          >
            <X size={20} />
          </button>
        </div>

        {/* Two-column layout */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Left: Details */}
          <div className="space-y-4">
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-content-muted mb-1">
                Summary
              </h3>
              <p className="text-content-secondary text-sm leading-relaxed">{workflow.summary}</p>
            </div>

            {workflow.entity && (
              <div>
                <h3 className="text-xs font-semibold uppercase tracking-wider text-content-muted mb-1">
                  Entity
                </h3>
                <p className="text-content-primary text-sm font-mono">{workflow.entity}</p>
              </div>
            )}

            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-content-muted mb-1">
                Timestamps
              </h3>
              <div className="flex items-center gap-1 text-content-muted text-xs">
                <Clock size={12} />
                <span>Created {timeAgo(workflow.created_at)}</span>
              </div>
              {workflow.updated_at && (
                <div className="flex items-center gap-1 text-content-muted text-xs mt-0.5">
                  <Clock size={12} />
                  <span>Updated {timeAgo(workflow.updated_at)}</span>
                </div>
              )}
            </div>

            {reasoningStr && (
              <div>
                <button
                  onClick={() => setReasoningExpanded((v) => !v)}
                  className="flex items-center gap-1 text-xs font-semibold uppercase tracking-wider text-content-muted hover:text-content-secondary transition-colors mb-1"
                >
                  <span>{reasoningExpanded ? '▾' : '▸'} Reasoning Chain</span>
                </button>
                {reasoningExpanded && (
                  <pre className="font-mono text-sm bg-surface-secondary rounded p-3 overflow-x-auto text-content-secondary whitespace-pre-wrap break-all">
                    {reasoningStr}
                  </pre>
                )}
              </div>
            )}
          </div>

          {/* Right: Agent Flow */}
          <div>
            {steps && steps.length > 0 ? (
              <div>
                <h3 className="text-xs font-semibold uppercase tracking-wider text-content-muted mb-3">
                  Agent Flow
                </h3>
                <AgentFlowDiagram steps={steps} currentStatus={workflow.status} />
              </div>
            ) : (
              <div className="flex items-center justify-center h-full text-content-muted text-sm">
                No agent flow defined for this workflow type.
              </div>
            )}
          </div>
        </div>

        {/* Action bar */}
        <div className="flex items-center gap-3 flex-wrap mt-6 pt-4 border-t border-border">
          <button
            disabled={actioning}
            onClick={onApprove}
            className={cn(
              'flex items-center gap-1.5 text-sm px-4 py-2 rounded-lg font-medium transition-colors',
              'bg-success text-white hover:bg-success/90 disabled:opacity-50 disabled:cursor-not-allowed'
            )}
          >
            <Check size={15} />
            Approve
          </button>
          <button
            disabled={actioning}
            onClick={onDismiss}
            className={cn(
              'flex items-center gap-1.5 text-sm px-4 py-2 rounded-lg font-medium transition-colors',
              'bg-surface-hover text-content-muted hover:bg-border disabled:opacity-50 disabled:cursor-not-allowed'
            )}
          >
            <X size={15} />
            Dismiss
          </button>

          {onAskAI && (
            <button
              onClick={() => onAskAI(`Analyze workflow: ${workflow.summary}`)}
              className="ml-auto flex items-center gap-1.5 text-sm px-4 py-2 rounded-lg font-medium bg-accent/10 text-accent hover:bg-accent/20 transition-colors"
            >
              <MessageSquare size={15} />
              Ask AI
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

export function WorkflowPanel({
  endpoint = '/agent-overview',
  workflowTypes,
  severityLevels,
  agentSteps,
  onAskAI,
}: WorkflowPanelProps) {
  const { data, loading, refetch } = useApi<AgentOverviewResponse | Workflow[]>(endpoint)

  const [statusFilter, setStatusFilter] = useState('all')
  const [severityFilter, setSeverityFilter] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedWorkflow, setSelectedWorkflow] = useState<Workflow | null>(null)
  const [actioning, setActioning] = useState(false)

  // Normalize response: the endpoint may return { workflows: [...] } or a plain array
  const allWorkflows: Workflow[] = Array.isArray(data)
    ? (data as Workflow[])
    : ((data as AgentOverviewResponse)?.workflows ?? [])

  // Compute available filter options
  const availableTypes = workflowTypes ?? [...new Set(allWorkflows.map((w) => w.workflow_type))]
  const availableSeverities = severityLevels ?? SEVERITY_OPTIONS.map((s) => s.value)

  // Filter workflows
  const filtered = allWorkflows.filter((w) => {
    if (statusFilter !== 'all' && w.status !== statusFilter) return false
    if (severityFilter !== 'all' && w.severity?.toLowerCase() !== severityFilter) return false
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase()
      if (
        !w.summary?.toLowerCase().includes(q) &&
        !w.workflow_type?.toLowerCase().includes(q) &&
        !w.entity?.toLowerCase().includes(q)
      )
        return false
    }
    return true
  })

  // Limit displayed types in the type filter to what's in data
  const typeFilterOptions = availableTypes.filter((t) =>
    allWorkflows.some((w) => w.workflow_type === t)
  )

  async function handleAction(workflow: Workflow, status: 'approved' | 'dismissed') {
    setActioning(true)
    try {
      const patchUrl = endpoint.replace('agent-overview', 'workflows') + `/${workflow.id}`
      await api.patch(patchUrl, { status })
      await refetch()
      setSelectedWorkflow(null)
    } catch (err) {
      console.error(`WorkflowPanel: failed to ${status} workflow ${workflow.id}`, err)
    } finally {
      setActioning(false)
    }
  }

  return (
    <div className="space-y-4">
      {/* Filter Bar */}
      <div className="flex flex-col sm:flex-row gap-3 flex-wrap">
        {/* Search */}
        <div className="relative flex-1 min-w-[200px]">
          <Search
            size={15}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-content-muted pointer-events-none"
          />
          <input
            type="text"
            placeholder="Search workflows..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-2 text-sm bg-surface-card border border-border rounded-lg text-content-primary placeholder:text-content-muted focus:outline-none focus:ring-1 focus:ring-accent/50 focus:border-accent/50 transition-colors"
          />
        </div>

        {/* Status filters */}
        <div className="flex items-center gap-1 flex-wrap">
          {STATUS_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => setStatusFilter(opt.value)}
              className={cn(
                'text-xs px-3 py-1.5 rounded-lg font-medium transition-colors border',
                statusFilter === opt.value
                  ? 'bg-accent text-white border-accent'
                  : 'bg-surface-card text-content-muted border-border hover:border-border-hover hover:text-content-secondary'
              )}
            >
              {opt.label}
            </button>
          ))}
        </div>

        {/* Severity filters */}
        <div className="flex items-center gap-1 flex-wrap">
          {SEVERITY_OPTIONS.filter(
            (opt) => opt.value === 'all' || availableSeverities.includes(opt.value)
          ).map((opt) => (
            <button
              key={opt.value}
              onClick={() => setSeverityFilter(opt.value)}
              className={cn(
                'text-xs px-3 py-1.5 rounded-lg font-medium transition-colors border',
                severityFilter === opt.value
                  ? 'bg-accent text-white border-accent'
                  : 'bg-surface-card text-content-muted border-border hover:border-border-hover hover:text-content-secondary'
              )}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* Type filter row (only shown if multiple types in data) */}
      {typeFilterOptions.length > 1 && (
        <div className="flex items-center gap-1 flex-wrap">
          <span className="text-xs text-content-muted mr-1">Type:</span>
          {typeFilterOptions.map((type) => (
            <button
              key={type}
              className="text-xs px-2.5 py-1 rounded border border-border bg-surface-card text-content-muted hover:border-accent/50 hover:text-content-secondary transition-colors"
            >
              {formatWorkflowType(type)}
            </button>
          ))}
        </div>
      )}

      {/* Cards Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-16 text-content-muted text-sm flex flex-col items-center gap-2">
          <AlertTriangle size={28} className="text-content-muted/40" />
          <span>No workflows found matching your filters.</span>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((workflow) => {
            const severityKey = workflow.severity?.toLowerCase() ?? 'medium'
            const badgeClass =
              severityBadgeClass[severityKey] ??
              'bg-surface-hover text-content-muted border-border'
            const statusKey = workflow.status?.toLowerCase() ?? ''
            const statusClass =
              statusBadgeClass[statusKey] ??
              'bg-surface-hover text-content-muted border-border'

            return (
              <div
                key={workflow.id}
                onClick={() => setSelectedWorkflow(workflow)}
                className="bg-surface-card border border-border rounded-lg p-4 cursor-pointer hover:border-accent/50 transition-colors"
              >
                {/* Type + severity row */}
                <div className="flex items-center gap-2 mb-2 flex-wrap">
                  <span className="text-xs font-semibold text-content-secondary bg-surface-hover px-2 py-0.5 rounded">
                    {formatWorkflowType(workflow.workflow_type)}
                  </span>
                  <span
                    className={cn(
                      'inline-flex items-center text-xs font-medium px-2 py-0.5 rounded-full border capitalize',
                      badgeClass
                    )}
                  >
                    {workflow.severity}
                  </span>
                </div>

                {/* Summary — 2-line truncate */}
                <p className="text-content-primary text-sm leading-snug mb-2 line-clamp-2">
                  {workflow.summary}
                </p>

                {/* Entity */}
                {workflow.entity && (
                  <p className="text-content-muted text-xs font-mono mb-2 truncate">
                    {workflow.entity}
                  </p>
                )}

                {/* Footer: timestamp + status */}
                <div className="flex items-center justify-between gap-2 pt-2 border-t border-border">
                  <div className="flex items-center gap-1 text-content-muted text-xs">
                    <Clock size={11} />
                    <span>{timeAgo(workflow.created_at)}</span>
                  </div>
                  <span
                    className={cn(
                      'inline-flex items-center text-xs font-medium px-2 py-0.5 rounded-full border capitalize',
                      statusClass
                    )}
                  >
                    {formatStatus(workflow.status)}
                  </span>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Detail Modal */}
      {selectedWorkflow && (
        <WorkflowDetailModal
          workflow={selectedWorkflow}
          agentSteps={agentSteps}
          onClose={() => setSelectedWorkflow(null)}
          onApprove={() => handleAction(selectedWorkflow, 'approved')}
          onDismiss={() => handleAction(selectedWorkflow, 'dismissed')}
          onAskAI={onAskAI}
          actioning={actioning}
          workflowEndpoint={endpoint}
        />
      )}
    </div>
  )
}
