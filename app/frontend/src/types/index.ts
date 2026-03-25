import type { LucideIcon } from 'lucide-react'
import type { LazyExoticComponent, ComponentType } from 'react'

export interface DemoConfig {
  name: string
  customer: string
  industry: string
  features: string[]
  layout: 'sidebar' | 'topnav' | 'dashboard'
  theme: string
  mode: 'light' | 'dark'
}

export interface RouteConfig {
  path: string
  label: string
  icon: LucideIcon
  page: LazyExoticComponent<ComponentType<unknown>>
}

export interface KPIMetric {
  label: string
  value: string | number
  change?: number
  trend?: 'up' | 'down' | 'flat'
  icon?: LucideIcon
  color?: string
}

export interface ColumnDef {
  key: string
  label: string
  type?: 'text' | 'number' | 'date' | 'badge' | 'link'
  sortable?: boolean
  filterable?: boolean
  width?: string
}

export interface RowAction {
  label: string
  icon?: LucideIcon
  onClick: (row: Record<string, unknown>) => void
  variant?: 'default' | 'destructive'
}

export interface ActionCardData {
  type: string
  id: string
  title: string
  details: Record<string, string>
  actions: string[]
}

export interface ActionCardConfig {
  table: string
  card_type: string
  id_col: string
  title_template: string
  actions: string[]
  detail_cols: Record<string, string>
}

export interface MapMarker {
  lat: number
  lng: number
  label?: string
  color?: string
  popup?: string
}

export interface MapRoute {
  points: [number, number][]
  color?: string
  animated?: boolean
}

export interface HeatmapData {
  points: [number, number, number][]
  radius?: number
  intensity?: number
}

export interface TimelineEvent {
  id: string
  timestamp: string | Date
  title: string
  description?: string
  type?: string
  severity?: 'low' | 'medium' | 'high' | 'critical'
}

export interface McpApprovalRequest {
  id: string
  tool_name: string
  arguments: Record<string, unknown>
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  thinking?: string
  toolCalls?: string[]
  actionCards?: ActionCardData[]
  suggestedActions?: string[]
  timestamp: Date
}

export interface UseApiOptions {
  autoFetch?: boolean
  params?: Record<string, string>
  pollInterval?: number
}

export interface UseApiResult<T> {
  data: T | null
  loading: boolean
  error: Error | null
  refetch: () => Promise<void>
}
