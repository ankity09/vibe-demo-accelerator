# VDA React Component Reference

Quick reference for building pages with VDA's component library. All components live in
`app/frontend/src/components/vda/`. Hooks are in `app/frontend/src/hooks/`.

For backend route patterns see [`examples/supply_chain_routes.py`](./supply_chain_routes.py).

---

## 1. Creating a New Page

**Step 1 — Create the page file** (`app/frontend/src/pages/MyPage.tsx`):

```tsx
import { KPIDashboard } from '@/components/vda/KPIDashboard'
import { useApi } from '@/hooks/useApi'

export function MyPage() {
  const { data, loading } = useApi<{ total: number }>('/my-endpoint')
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-content-primary">My Page</h1>
      <KPIDashboard metrics={[{ label: 'Total', value: data?.total ?? 0 }]} loading={loading} />
    </div>
  )
}
```

**Step 2 — Register in `App.tsx`:**

```tsx
import { lazy } from 'react'
import { MyIcon } from 'lucide-react'

const MyPage = lazy(() => import('./pages/MyPage').then(m => ({ default: m.MyPage })))

export const routes: RouteConfig[] = [
  // ...existing routes...
  { path: '/my-page', label: 'My Page', icon: MyIcon, page: MyPage },
]
```

---

## 2. Component Quick Reference

### KPIDashboard
Grid of animated metric cards with trend indicators.

```tsx
import { KPIDashboard } from '@/components/vda/KPIDashboard'
import { TrendingUp } from 'lucide-react'

<KPIDashboard
  metrics={[
    { label: 'Revenue', value: '$2.4M', change: 8.3, trend: 'up', icon: TrendingUp },
    { label: 'Orders',  value: 1842,   change: -2.1, trend: 'down' },
    { label: 'Status',  value: 'OK',   trend: 'flat', color: '#10b981' },
  ]}
  columns={4}   // 3 | 4 | 5 — default 4
  loading={false}
/>
```

---

### DataExplorer
Paginated, sortable, searchable table fed by an API endpoint.

```tsx
import { DataExplorer } from '@/components/vda/DataExplorer'
import type { ColumnDef } from '@/types'

const columns: ColumnDef[] = [
  { key: 'id',      label: 'ID',     type: 'text' },
  { key: 'name',    label: 'Name',   type: 'text',   sortable: true },
  { key: 'status',  label: 'Status', type: 'badge' },   // auto-colors critical/high/medium/low
  { key: 'amount',  label: 'Amount', type: 'number', sortable: true },
  { key: 'created', label: 'Date',   type: 'date' },
]

<DataExplorer
  endpoint="/orders"    // relative to axios baseURL (/api)
  columns={columns}
  searchable
  pageSize={25}
  onRowClick={(row) => console.log(row)}
  actions={[
    { label: 'Edit',   icon: PencilIcon, onClick: (row) => handleEdit(row) },
    { label: 'Delete', icon: TrashIcon,  onClick: (row) => handleDelete(row), variant: 'destructive' },
  ]}
/>
```

---

### AgentChat
Full MAS streaming chat with reasoning blocks, tool call steps, action cards, and suggested prompts. Do NOT rebuild — customize props only.

```tsx
import { AgentChat } from '@/components/vda/AgentChat'

<AgentChat
  endpoint="/api/chat"                   // default
  welcomeTitle="Ask about your fleet"
  welcomeSubtitle="Powered by Databricks MAS"
  suggestedPrompts={[
    'Show me critical alerts',
    'Create a work order for machine M-042',
  ]}
  agentNameMap={{
    'my_genie_space':         'Data Query',
    'mcp-lakebase-connection': 'Database (write)',
  }}
  showReasoning={true}    // collapsible thinking blocks
  autoApproveMcp={true}   // auto-approve MCP tool calls
/>
```

---

### WorkflowPanel
Workflow cards with status/severity filters, search, and a detail modal with agent flow diagram. Do NOT rebuild — customize `agentSteps` mapping.

```tsx
import { WorkflowPanel } from '@/components/vda/WorkflowPanel'

<WorkflowPanel
  endpoint="/agent-overview"   // relative to axios baseURL
  agentSteps={{
    maintenance_request: ['Detect anomaly', 'Assess severity', 'Create work order', 'Notify technician'],
    parts_order:         ['Check inventory', 'Source supplier', 'Generate PO', 'Confirm delivery'],
  }}
  onAskAI={(prompt) => navigate('/chat', { state: { prompt } })}
/>
```

---

### ExceptionManager
Alert triage list with acknowledge/escalate/resolve/dismiss actions.

```tsx
import { ExceptionManager } from '@/components/vda/ExceptionManager'

<ExceptionManager
  endpoint="/exceptions"   // GET returns Exception[], PATCH /{id} accepts { status }
  actions={['acknowledge', 'escalate', 'resolve', 'dismiss']}
  severityColors={{ critical: 'red', high: 'amber', medium: 'blue', low: 'green' }}
  onAskAI={(prompt) => sendToChat(prompt)}
/>
// Exception shape: { id, title, description?, severity, entity?, timestamp, status? }
```

---

### GeoView
Leaflet map with dark CARTO tile layer, custom colored markers, and polyline routes.

```tsx
import { GeoView } from '@/components/vda/GeoView'
import type { MapMarker, MapRoute } from '@/types'

<GeoView
  center={[39.8, -98.5]}   // [lat, lng] — default: US center
  zoom={4}
  markers={[
    { lat: 47.6, lng: -122.3, label: 'Seattle', color: '#10b981', popup: 'Warehouse A' },
    { lat: 33.7, lng: -84.4,  label: 'Atlanta', color: '#ef4444' },
  ]}
  routes={[
    { points: [[47.6, -122.3], [33.7, -84.4]], color: '#f59e0b', animated: true },
  ]}
  onMarkerClick={(marker) => console.log(marker)}
  className="h-[500px]"   // override default h-[400px]
/>
// Note: call map.invalidateSize() after tab switch (MapInvalidator does this automatically)
```

---

### TimelineView
Chronological event feed grouped by day or hour.

```tsx
import { TimelineView } from '@/components/vda/TimelineView'
import type { TimelineEvent } from '@/types'

// TimelineEvent: { id, timestamp, title, description?, type?, severity?: 'low'|'medium'|'high'|'critical' }
<TimelineView
  events={events}
  groupBy="day"      // 'day' | 'hour' — default 'day'
  maxItems={20}      // show N items with "Show more" button
  onEventClick={(event) => setSelected(event)}
/>
```

---

### MetricsBar
Compact horizontal metrics strip — good for page headers.

```tsx
import { MetricsBar } from '@/components/vda/MetricsBar'
import { Activity } from 'lucide-react'

<MetricsBar
  metrics={[
    { label: 'Uptime',     value: '99.7%', icon: Activity },
    { label: 'Throughput', value: '1.2K/hr' },
    { label: 'Latency',    value: '45ms' },
  ]}
  variant="compact"   // 'compact' | 'full' — default 'compact'
/>
```

---

### ThemeToggle
Light/dark toggle + theme picker. Drop into the nav header via `App.tsx` `headerRight` prop.

```tsx
import { ThemeToggle } from '@/components/vda/ThemeToggle'

<ThemeToggle position="nav" />       // in AppShell headerRight
<ThemeToggle position="floating" />  // fixed bottom-right button (dark/light only)
```

---

### NotesPanel
Slide-in notes drawer scoped to any entity. Backend needs `GET /notes?entity_type=X&entity_id=Y` and `POST /notes`.

```tsx
import { NotesPanel } from '@/components/vda/NotesPanel'

const [notesOpen, setNotesOpen] = useState(false)

<button onClick={() => setNotesOpen(true)}>Notes</button>
<NotesPanel
  entityType="asset"
  entityId={asset.id}
  endpoint="/notes"   // default
  open={notesOpen}
  onClose={() => setNotesOpen(false)}
/>
```

---

### LiveFeedIndicator
Streaming status badge with optional start/stop controls and per-stream stats.

```tsx
import { LiveFeedIndicator } from '@/components/vda/LiveFeedIndicator'

<LiveFeedIndicator />                                    // dot + "Live"/"Offline" label
<LiveFeedIndicator showControls showStats pollInterval={15000} />
```

---

### ActionCard
Entity card emitted by MAS chat. Normally rendered automatically inside `AgentChat` — use directly only for custom chat UIs.

```tsx
import { ActionCard } from '@/components/vda/ActionCard'
import type { ActionCardData } from '@/types'

// ActionCardData: { type, id, title, details: Record<string,string>, actions: string[] }
<ActionCard
  card={{ type: 'work_order', id: 'WO-123', title: 'Replace bearing', details: { Priority: 'High' }, actions: ['approve', 'dismiss'] }}
  onAction={(action, id) => api.patch(`/workflows/${id}`, { status: action })}
/>
```

---

## 3. Hooks Quick Reference

### useApi
```tsx
const { data, loading, error, refetch } = useApi<MyType[]>('/endpoint')

// With options:
const { data } = useApi<Stats>('/stats', {
  autoFetch: true,
  params: { status: 'active', limit: '50' },   // query string params
  pollInterval: 15000,                          // ms — auto-refetch while mounted
})
```

### useSSE
Used internally by `AgentChat`. Use directly for custom streaming UIs:
```tsx
const { send, abort, isStreaming } = useSSE('/api/chat', {
  onThinking: (text) => appendThinking(text),
  onDelta:    (text) => appendResponse(text),
  onToolCall: (tool) => showStep(tool),
  onDone:     ()     => finishStream(),
  onError:    (msg)  => showError(msg),
  onSessionExpired: () => window.location.reload(),
})

await send({ message: 'Hello', history: [], auto_approve_mcp: true })
```

### useTheme
```tsx
const { theme, mode, setTheme, toggleMode } = useTheme()
// theme: 'industrial' | 'medical' | 'corporate' | 'neutral'
// mode:  'dark' | 'light'
setTheme('industrial')
toggleMode()
```

### useLiveFeed
```tsx
const { status, loading, start, stop } = useLiveFeed(15000)
// status: { running: boolean, elapsed_seconds: number, stats: Record<stream, { rows_inserted, errors }> }
await start()
await stop()
```

---

## 4. Theme Tokens (Tailwind Classes)

| Token | Class | Usage |
|-------|-------|-------|
| Page background | `bg-surface-primary` | Page root, sidebar |
| Secondary bg | `bg-surface-secondary` | Topbar, input rows |
| Card background | `bg-surface-card` | Cards, modals, tables |
| Hover state | `bg-surface-hover` | Row hover, button hover |
| Primary text | `text-content-primary` | Headlines, values |
| Secondary text | `text-content-secondary` | Body copy, descriptions |
| Muted text | `text-content-muted` | Labels, metadata |
| Accent (CTA) | `text-accent` / `bg-accent` | Buttons, links, indicators |
| Accent hover | `bg-accent-hover` | Button hover state |
| Border | `border-border` | Cards, dividers |
| Border hover | `border-border-hover` | Interactive card hover |
| Success | `text-success` / `bg-success` | Status: ok, resolved |
| Warning | `text-warning` / `bg-warning` | Status: high, pending |
| Error | `text-error` / `bg-error` | Status: critical, failed |
| Info | `text-info` / `bg-info` | Status: medium, in-progress |
| Font: UI | `font-sans` | Plus Jakarta Sans |
| Font: Code/Data | `font-mono` | Space Mono |
| Font: Headlines | `font-display` | Playfair Display |

Semantic opacity variants: `bg-error/10`, `text-success/80`, etc.

---

## 5. Layout Options

Set `layout` in `app/frontend/src/demo-config.ts`:

```ts
export const demoConfig: DemoConfig = {
  name: 'Acme Predictive Maintenance',
  customer: 'Acme Corp',
  industry: 'Manufacturing',
  features: [],
  layout: 'sidebar',     // 'sidebar' | 'topnav' | 'dashboard'
  theme: 'industrial',   // 'industrial' | 'medical' | 'corporate' | 'neutral'
  mode: 'dark',          // 'dark' | 'light'
}
```

| Layout | Description | Best for |
|--------|-------------|----------|
| `sidebar` | Fixed left nav with icon + label, scrollable content area | Multi-page demos with 4+ pages |
| `topnav` | Horizontal nav bar across the top | Simpler demos, 2–4 pages |
| `dashboard` | Full-width grid, no persistent nav | Single-page command center |

`AppShell` in `App.tsx` reads `demoConfig.layout` and selects the matching layout automatically.
To change the layout, update only `demo-config.ts`.
