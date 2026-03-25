# VDA React Foundation + Component Library — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the single-HTML frontend with a React + Vite app featuring 12 VDA compound components, 4 theme presets with light/dark mode, 3 composable layouts, and an extracted backend route system.

**Architecture:** React 18 + Vite frontend with shadcn/ui primitives, VDA compound components, and CSS variable-based theming. Backend core modules untouched — chat and workflow routes extracted from the 1509-line main.py into separate files. FastAPI serves the React build from `frontend/dist/` in production; Vite proxies `/api` to FastAPI in dev.

**Tech Stack:** React 18, Vite 5, TypeScript 5, Tailwind CSS 3, shadcn/ui, React Router v6, Zustand, Axios, Framer Motion, Lucide React

**Spec:** `docs/superpowers/specs/2026-03-25-vda-react-redesign-design.md`

**Scope:** Phases 1-2 from the spec (Foundation + Component Library). Phases 3-5 (Feature System, Wizard, Dev Loop) are a separate plan.

---

## File Map

### New Files (Frontend)

| File | Responsibility |
|---|---|
| `app/frontend/package.json` | Dependencies and scripts |
| `app/frontend/index.html` | Vite entry point (~10 lines) |
| `app/frontend/vite.config.ts` | Dev server, proxy, build config |
| `app/frontend/tailwind.config.ts` | VDA theme tokens mapped to Tailwind |
| `app/frontend/tsconfig.json` | TypeScript strict mode config |
| `app/frontend/postcss.config.js` | PostCSS with Tailwind + autoprefixer |
| `app/frontend/src/main.tsx` | React root, router, theme init |
| `app/frontend/src/App.tsx` | AppShell + route config array |
| `app/frontend/src/demo-config.ts` | Placeholder demo config (vibe-generated per demo) |
| `app/frontend/src/vite-env.d.ts` | Vite client types |
| `app/frontend/src/styles/globals.css` | Tailwind directives + CSS variable structure |
| `app/frontend/src/styles/themes/industrial.css` | Navy/amber theme (light + dark) |
| `app/frontend/src/styles/themes/medical.css` | Slate/teal theme (light + dark) |
| `app/frontend/src/styles/themes/corporate.css` | Navy/blue theme (light + dark) |
| `app/frontend/src/styles/themes/neutral.css` | Charcoal/emerald theme (light + dark) |
| `app/frontend/src/lib/api.ts` | Axios instance with baseURL |
| `app/frontend/src/lib/utils.ts` | `cn()` class merge + formatters |
| `app/frontend/src/lib/constants.ts` | Re-exports from demo-config |
| `app/frontend/src/hooks/useTheme.ts` | Theme/mode toggle, localStorage persistence |
| `app/frontend/src/hooks/useApi.ts` | Fetch wrapper with loading/error/refetch |
| `app/frontend/src/hooks/useSSE.ts` | SSE streaming for full MAS protocol |
| `app/frontend/src/hooks/useLiveFeed.ts` | Streaming status polling |
| `app/frontend/src/stores/chatStore.ts` | Zustand chat state + history |
| `app/frontend/src/layouts/AppShell.tsx` | Layout switcher reading config |
| `app/frontend/src/layouts/SidebarLayout.tsx` | Collapsible sidebar + header |
| `app/frontend/src/layouts/TopNavLayout.tsx` | Horizontal nav bar |
| `app/frontend/src/layouts/DashboardLayout.tsx` | Full-screen + floating menu |
| `app/frontend/src/pages/Dashboard.tsx` | Placeholder dashboard page |
| `app/frontend/src/pages/Chat.tsx` | Chat page wrapping AgentChat |
| `app/frontend/src/pages/Workflows.tsx` | Workflows page wrapping WorkflowPanel |
| `app/frontend/src/components/vda/AgentChat.tsx` | Full MAS streaming chat |
| `app/frontend/src/components/vda/WorkflowPanel.tsx` | Workflow cards + detail modal |
| `app/frontend/src/components/vda/KPIDashboard.tsx` | KPI metric cards grid |
| `app/frontend/src/components/vda/DataExplorer.tsx` | Paginated sortable table |
| `app/frontend/src/components/vda/ExceptionManager.tsx` | Alert triage interface |
| `app/frontend/src/components/vda/GeoView.tsx` | Map wrapper (Leaflet/Mapbox) |
| `app/frontend/src/components/vda/TimelineView.tsx` | Chronological event timeline |
| `app/frontend/src/components/vda/MetricsBar.tsx` | Compact horizontal metrics |
| `app/frontend/src/components/vda/ThemeToggle.tsx` | Light/dark mode switch |
| `app/frontend/src/components/vda/NotesPanel.tsx` | Entity-attached notes sidebar |
| `app/frontend/src/components/vda/LiveFeedIndicator.tsx` | Streaming status bar |
| `app/frontend/src/components/vda/ActionCard.tsx` | Entity card from agent chat |
| `app/frontend/src/types/index.ts` | Shared TypeScript interfaces |

### New Files (Backend)

| File | Responsibility |
|---|---|
| `app/backend/routes/__init__.py` | Package init |
| `app/backend/routes/chat.py` | Chat endpoints extracted from main.py |
| `app/backend/routes/workflows.py` | Workflow + exceptions + briefing endpoints |

### Modified Files

| File | Change |
|---|---|
| `app/backend/main.py` | Slim to assembly — import routers, mount static from `frontend/dist` |

### Deleted Files

| File | Reason |
|---|---|
| `app/frontend/src/index.html` | 157KB monolith replaced by React app |

---

## Task 1: Initialize Vite Project

**Files:**
- Create: `app/frontend/package.json`
- Create: `app/frontend/index.html`
- Create: `app/frontend/vite.config.ts`
- Create: `app/frontend/tsconfig.json`
- Create: `app/frontend/postcss.config.js`
- Create: `app/frontend/src/vite-env.d.ts`
- Create: `app/frontend/src/main.tsx`

- [ ] **Step 1: Scaffold Vite React-TS project**

Run from project root. Do NOT use `npm create vite` (it creates a new directory). Instead, manually create the files:

```bash
cd app/frontend
npm init -y
npm install react@^18.3 react-dom@^18.3 react-router-dom@^6.26 zustand@^4.5 axios@^1.7 framer-motion@^11.5 lucide-react@^0.441 react-markdown@^9.0 remark-gfm@^4.0 clsx@^2.1 tailwind-merge@^2.5
npm install -D vite@^5.4 @vitejs/plugin-react@^4.3 typescript@^5.6 tailwindcss@^3.4 postcss@^8.4 autoprefixer@^10.4 @types/react@^18.3 @types/react-dom@^18.3
```

- [ ] **Step 2: Create package.json scripts**

Ensure `package.json` has these scripts:
```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc --noEmit && vite build",
    "preview": "vite preview",
    "typecheck": "tsc --noEmit"
  }
}
```

- [ ] **Step 3: Create Vite config with API proxy**

Write `app/frontend/vite.config.ts`:
```ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
  },
})
```

- [ ] **Step 4: Create TypeScript config**

Write `app/frontend/tsconfig.json`:
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src"]
}
```

- [ ] **Step 5: Create PostCSS config**

Write `app/frontend/postcss.config.js`:
```js
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

- [ ] **Step 6: Create Vite entry point**

Write `app/frontend/index.html`:
```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>VDA Demo</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

Write `app/frontend/src/vite-env.d.ts`:
```ts
/// <reference types="vite/client" />
```

- [ ] **Step 7: Create minimal React entry**

Write `app/frontend/src/main.tsx`:
```tsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './styles/globals.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <div>VDA React app running</div>
  </StrictMode>,
)
```

- [ ] **Step 8: Verify Vite starts**

```bash
cd app/frontend && npm run dev
```
Expected: Vite dev server starts on port 5173, browser shows "VDA React app running".

- [ ] **Step 9: Commit**

```bash
git add app/frontend/package.json app/frontend/package-lock.json app/frontend/index.html app/frontend/vite.config.ts app/frontend/tsconfig.json app/frontend/postcss.config.js app/frontend/src/vite-env.d.ts app/frontend/src/main.tsx
git commit -m "feat: initialize React + Vite project with dependencies"
```

---

## Task 2: Theme System

**Files:**
- Create: `app/frontend/tailwind.config.ts`
- Create: `app/frontend/src/styles/globals.css`
- Create: `app/frontend/src/styles/themes/industrial.css`
- Create: `app/frontend/src/styles/themes/medical.css`
- Create: `app/frontend/src/styles/themes/corporate.css`
- Create: `app/frontend/src/styles/themes/neutral.css`

- [ ] **Step 1: Create Tailwind config with VDA tokens**

Write `app/frontend/tailwind.config.ts` per spec Section 3 — map CSS variables to `surface`, `content`, `accent` namespaces. Include `content: ['./index.html', './src/**/*.{ts,tsx}']`.

- [ ] **Step 2: Create globals.css**

Write `app/frontend/src/styles/globals.css` with Tailwind directives (`@tailwind base/components/utilities`), base body styles using CSS variables, scrollbar styling, and imports for all 4 theme files.

- [ ] **Step 3: Create industrial theme (dark + light)**

Write `app/frontend/src/styles/themes/industrial.css` with `[data-theme="industrial-dark"]` and `[data-theme="industrial-light"]` selectors. Full variable set per spec: `--bg-primary` through `--border-hover`, plus badge colors, shadows, ring colors.

Navy/amber palette: dark base `#0A0F1C`, accent `#F59E0B`.

- [ ] **Step 4: Create medical theme (dark + light)**

Write `app/frontend/src/styles/themes/medical.css`. Slate/teal palette: dark base `#0F172A`, accent `#14B8A6`.

- [ ] **Step 5: Create corporate theme (dark + light)**

Write `app/frontend/src/styles/themes/corporate.css`. Navy/blue palette: dark base `#0C1222`, accent `#3B82F6`.

- [ ] **Step 6: Create neutral theme (dark + light)**

Write `app/frontend/src/styles/themes/neutral.css`. Charcoal/emerald palette: dark base `#111111`, accent `#10B981`.

- [ ] **Step 7: Verify themes load**

Update `main.tsx` to import globals.css (already done in Task 1). Set `data-theme="industrial-dark"` on `<html>`. Add a test div with `className="bg-surface-primary text-content-primary"`. Verify it renders with correct colors.

- [ ] **Step 8: Commit**

```bash
git add app/frontend/tailwind.config.ts app/frontend/src/styles/
git commit -m "feat: add VDA theme system — 4 themes with light/dark variants"
```

---

## Task 3: Lib Utilities

**Files:**
- Create: `app/frontend/src/lib/api.ts`
- Create: `app/frontend/src/lib/utils.ts`
- Create: `app/frontend/src/types/index.ts`
- Create: `app/frontend/src/demo-config.ts`
- Create: `app/frontend/src/lib/constants.ts`

- [ ] **Step 1: Create shared TypeScript types**

Write `app/frontend/src/types/index.ts` with all interfaces from spec Section 2: `KPIMetric`, `ColumnDef`, `RowAction`, `ActionCardData`, `ActionCardConfig`, `MapMarker`, `MapRoute`, `HeatmapData`, `TimelineEvent`, `McpApprovalRequest`, `RouteConfig`, `DemoConfig`, and all component props interfaces.

- [ ] **Step 2: Create Axios API client**

Write `app/frontend/src/lib/api.ts`:
```ts
import axios from 'axios'

export const api = axios.create({
  baseURL: import.meta.env.DEV ? '' : '',
  headers: { 'Content-Type': 'application/json' },
})
```

BaseURL is empty because Vite proxy handles `/api` routing in dev, and in production FastAPI serves both.

- [ ] **Step 3: Create cn() utility**

Write `app/frontend/src/lib/utils.ts`:
```ts
import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatNumber(n: number): string {
  return new Intl.NumberFormat('en-US').format(n)
}

export function formatPercent(n: number): string {
  return `${n >= 0 ? '+' : ''}${n.toFixed(1)}%`
}

export function timeAgo(date: string | Date): string {
  const seconds = Math.floor((Date.now() - new Date(date).getTime()) / 1000)
  if (seconds < 60) return 'just now'
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`
  return `${Math.floor(seconds / 86400)}d ago`
}
```

- [ ] **Step 4: Create placeholder demo config**

Write `app/frontend/src/demo-config.ts`:
```ts
import type { DemoConfig } from '@/types'

export const demoConfig: DemoConfig = {
  name: 'VDA Demo',
  customer: 'Demo Customer',
  industry: 'General',
  features: [],
  layout: 'sidebar',
  theme: 'neutral',
  mode: 'dark',
}
```

Write `app/frontend/src/lib/constants.ts`:
```ts
export { demoConfig } from '@/demo-config'
```

- [ ] **Step 5: Type check**

```bash
cd app/frontend && npx tsc --noEmit
```
Expected: zero errors.

- [ ] **Step 6: Commit**

```bash
git add app/frontend/src/lib/ app/frontend/src/types/ app/frontend/src/demo-config.ts
git commit -m "feat: add lib utilities, TypeScript types, and demo config"
```

---

## Task 4: useTheme Hook

**Files:**
- Create: `app/frontend/src/hooks/useTheme.ts`

- [ ] **Step 1: Implement useTheme**

Write `app/frontend/src/hooks/useTheme.ts`:
```ts
import { useCallback, useEffect, useState } from 'react'

type Theme = 'industrial' | 'medical' | 'corporate' | 'neutral'
type Mode = 'light' | 'dark'

const STORAGE_KEY_THEME = 'vda-theme'
const STORAGE_KEY_MODE = 'vda-mode'

export function useTheme(defaultTheme: Theme = 'neutral', defaultMode: Mode = 'dark') {
  const [theme, setThemeState] = useState<Theme>(() => {
    return (localStorage.getItem(STORAGE_KEY_THEME) as Theme) || defaultTheme
  })
  const [mode, setModeState] = useState<Mode>(() => {
    return (localStorage.getItem(STORAGE_KEY_MODE) as Mode) || defaultMode
  })

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', `${theme}-${mode}`)
    localStorage.setItem(STORAGE_KEY_THEME, theme)
    localStorage.setItem(STORAGE_KEY_MODE, mode)
  }, [theme, mode])

  const setTheme = useCallback((t: Theme) => setThemeState(t), [])
  const toggleMode = useCallback(() => {
    setModeState((m) => (m === 'dark' ? 'light' : 'dark'))
  }, [])

  return { theme, mode, setTheme, toggleMode }
}
```

- [ ] **Step 2: Type check**

```bash
cd app/frontend && npx tsc --noEmit
```

- [ ] **Step 3: Commit**

```bash
git add app/frontend/src/hooks/useTheme.ts
git commit -m "feat: add useTheme hook with localStorage persistence"
```

---

## Task 5: useApi Hook

**Files:**
- Create: `app/frontend/src/hooks/useApi.ts`

- [ ] **Step 1: Implement useApi**

Write `app/frontend/src/hooks/useApi.ts` per spec: generic `useApi<T>` returning `{ data, loading, error, refetch }`. Supports `autoFetch`, `params`, and `pollInterval` options. Does NOT throw on error — sets `error` state. Uses the Axios instance from `lib/api.ts`.

- [ ] **Step 2: Type check**

```bash
cd app/frontend && npx tsc --noEmit
```

- [ ] **Step 3: Commit**

```bash
git add app/frontend/src/hooks/useApi.ts
git commit -m "feat: add useApi hook with loading/error state and polling"
```

---

## Task 6: AppShell + Layouts

**Files:**
- Create: `app/frontend/src/layouts/AppShell.tsx`
- Create: `app/frontend/src/layouts/SidebarLayout.tsx`
- Create: `app/frontend/src/layouts/TopNavLayout.tsx`
- Create: `app/frontend/src/layouts/DashboardLayout.tsx`

- [ ] **Step 1: Create SidebarLayout**

Write `app/frontend/src/layouts/SidebarLayout.tsx`: fixed left sidebar (280px, collapsible to 64px), top header bar with demo name + right-side slot (for ThemeToggle). Sidebar renders nav links from a `routes` prop (`RouteConfig[]`). Active route highlighted. Uses Lucide icons. Uses `surface`/`content` theme tokens throughout.

Key elements:
- Collapsible toggle button at sidebar bottom
- Logo/demo name at top of sidebar
- Nav links with icon + label (label hidden when collapsed)
- Active link has `bg-accent/10` background and `text-accent` color
- Header bar spans the remaining width

- [ ] **Step 2: Create TopNavLayout**

Write `app/frontend/src/layouts/TopNavLayout.tsx`: horizontal nav bar with logo on left, page links centered, right-side slot. Full-width content below.

- [ ] **Step 3: Create DashboardLayout**

Write `app/frontend/src/layouts/DashboardLayout.tsx`: no persistent nav. Floating hamburger button (top-left) opens a slide-out drawer with nav links. Maximum content area.

- [ ] **Step 4: Create AppShell**

Write `app/frontend/src/layouts/AppShell.tsx`:
```tsx
import type { RouteConfig } from '@/types'
import { SidebarLayout } from './SidebarLayout'
import { TopNavLayout } from './TopNavLayout'
import { DashboardLayout } from './DashboardLayout'

interface AppShellProps {
  layout: 'sidebar' | 'topnav' | 'dashboard'
  demoName: string
  routes: RouteConfig[]
  logo?: React.ReactNode
  headerRight?: React.ReactNode
  children: React.ReactNode
}

export function AppShell({ layout, children, ...props }: AppShellProps) {
  switch (layout) {
    case 'topnav':
      return <TopNavLayout {...props}>{children}</TopNavLayout>
    case 'dashboard':
      return <DashboardLayout {...props}>{children}</DashboardLayout>
    default:
      return <SidebarLayout {...props}>{children}</SidebarLayout>
  }
}
```

- [ ] **Step 5: Type check and visual verify**

```bash
cd app/frontend && npx tsc --noEmit
```

Update `main.tsx` to render AppShell with a test route. Verify all 3 layouts render by temporarily switching the layout prop.

- [ ] **Step 6: Commit**

```bash
git add app/frontend/src/layouts/
git commit -m "feat: add AppShell with sidebar, topnav, and dashboard layouts"
```

---

## Task 7: Route System + App.tsx + Pages

**Files:**
- Create: `app/frontend/src/App.tsx`
- Create: `app/frontend/src/pages/Dashboard.tsx`
- Create: `app/frontend/src/pages/Chat.tsx`
- Create: `app/frontend/src/pages/Workflows.tsx`
- Modify: `app/frontend/src/main.tsx`

- [ ] **Step 1: Create placeholder pages**

Write `app/frontend/src/pages/Dashboard.tsx`:
```tsx
export function Dashboard() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-content-primary">Dashboard</h1>
      <p className="text-content-secondary">Dashboard content will be generated by vibe based on demo config.</p>
    </div>
  )
}
```

Write similar placeholders for `Chat.tsx` and `Workflows.tsx`.

- [ ] **Step 2: Create App.tsx with route config**

Write `app/frontend/src/App.tsx` per spec Section 4:
- Import `lazy` and `Suspense` from React
- Import `BrowserRouter`, `Routes`, `Route` from react-router-dom
- Define `routes` array with `RouteConfig` entries for Dashboard, Chat, Workflows
- Render `AppShell` wrapping `Routes` with lazy-loaded pages
- Read layout from `demoConfig`
- Render `ThemeToggle` in the header right slot (placeholder div for now)

- [ ] **Step 3: Update main.tsx**

Replace the test div in `main.tsx` with `<App />`:
```tsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { App } from './App'
import './styles/globals.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
```

- [ ] **Step 4: Verify routing works**

```bash
cd app/frontend && npm run dev
```
Expected: App loads with sidebar layout, three nav links. Clicking each navigates to the correct page. URL changes to `/`, `/chat`, `/workflows`.

- [ ] **Step 5: Verify build**

```bash
cd app/frontend && npm run build
```
Expected: clean build to `dist/`.

- [ ] **Step 6: Commit**

```bash
git add app/frontend/src/App.tsx app/frontend/src/pages/ app/frontend/src/main.tsx
git commit -m "feat: add route system with App.tsx and placeholder pages"
```

---

## Task 8: Backend Route Extraction

**Files:**
- Create: `app/backend/routes/__init__.py`
- Create: `app/backend/routes/chat.py`
- Create: `app/backend/routes/workflows.py`
- Modify: `app/backend/main.py`

This is the most delicate task — moving code from the 1509-line `main.py` into separate route files without breaking any endpoints.

- [ ] **Step 1: Create routes package**

Write `app/backend/routes/__init__.py` (empty file).

- [ ] **Step 2: Extract chat routes**

Create `app/backend/routes/chat.py`. Move from `main.py`:
- `_chat_history`, `_chat_session_id` globals
- `_ensure_chat_session()`, `_new_chat_session()`, `_save_chat_message()`, `_load_chat_history()`, `_clear_chat_history()` functions
- `POST /api/chat` → `@router.post("/chat")`
- `GET /api/chat/history` → `@router.get("/chat/history")`
- `POST /api/chat/clear` → `@router.post("/chat/clear")`

The router imports core modules the same way `main.py` does:
```python
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from backend.core.streaming import stream_mas_chat, _sse_keepalive, get_mcp_pending, clear_mcp_pending
from backend.core import run_pg_query, write_pg, _get_mas_auth
```

Use `router = APIRouter()` — it will be mounted at `/api` prefix in `main.py`.

- [ ] **Step 3: Extract workflow + exception + briefing routes**

Create `app/backend/routes/workflows.py`. Move from `main.py`:
- `GET /api/agent-overview` → `@router.get("/agent-overview")`
- `GET /api/workflows/{workflow_id}` → `@router.get("/workflows/{workflow_id}")`
- `PATCH /api/workflows/{workflow_id}` → `@router.patch("/workflows/{workflow_id}")`
- `GET /api/exceptions` → `@router.get("/exceptions")`
- `POST /api/exceptions` → `@router.post("/exceptions")`
- `PATCH /api/exceptions/{exception_id}` → `@router.patch("/exceptions/{exception_id}")`
- `GET /api/briefing` → `@router.get("/briefing")`
- `GET /api/briefing/stream` → `@router.get("/briefing/stream")`
- `_enrich_workflow()` helper

- [ ] **Step 4: Slim main.py**

Update `main.py`:
1. Remove all moved functions and endpoints
2. Add imports for the new routers
3. Mount routers: `app.include_router(chat_router, prefix="/api")`, `app.include_router(workflow_router, prefix="/api")`
4. Keep: `lifespan`, architecture endpoints, demo config helpers, SPA serving
5. Update static mount to serve from `frontend/dist`:
```python
_frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(_frontend_dir):
    app.mount("/", StaticFiles(directory=_frontend_dir, html=True), name="static")
```

**CRITICAL:** The architecture endpoints (`/api/architecture`, `/api/architecture/table-data`) and demo config helpers stay in `main.py` for now — they are domain-specific and will be moved in Plan 2 when the feature system is built. Only extract the generic routes (chat, workflows, exceptions, briefing).

- [ ] **Step 5: Verify no endpoints broke**

```bash
cd app && python -c "from backend.main import app; print('OK')"
```

Then start the server and verify each endpoint still responds:
```bash
cd app && uvicorn backend.main:app --port 8000 &
# Test endpoints respond (will get auth errors but should not 404):
curl -s http://localhost:8000/api/health | head -c 200
curl -s -X POST http://localhost:8000/api/chat -H 'Content-Type: application/json' -d '{"message":"test"}' | head -c 200
curl -s http://localhost:8000/api/agent-overview | head -c 200
```

- [ ] **Step 6: Commit**

```bash
git add app/backend/routes/ app/backend/main.py
git commit -m "refactor: extract chat and workflow routes from main.py into separate files"
```

---

## Task 9: useSSE Hook + Chat Store

**Files:**
- Create: `app/frontend/src/hooks/useSSE.ts`
- Create: `app/frontend/src/stores/chatStore.ts`

- [ ] **Step 1: Implement useSSE**

Write `app/frontend/src/hooks/useSSE.ts` implementing the full SSE protocol from spec Section 2. The hook:
- Takes `UseSSEOptions` with callbacks for all 11 event types
- Returns `{ send, abort, isStreaming }`
- `send(body)` opens a `fetch()` call to the endpoint, reads the response as a stream
- Parses `data: {...}` lines, dispatches to the matching callback based on `event` field
- Handles `[DONE]` marker to close the stream
- Handles `mcp_approval` events (passes to callback, which can resume via a separate `send`)
- `abort()` cancels the in-flight fetch

SSE parsing pattern:
```ts
const reader = response.body!.getReader()
const decoder = new TextDecoder()
let buffer = ''

while (true) {
  const { done, value } = await reader.read()
  if (done) break
  buffer += decoder.decode(value, { stream: true })
  const lines = buffer.split('\n')
  buffer = lines.pop() || ''
  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const data = line.slice(6)
      if (data === '[DONE]') { options.onDone(); return }
      const parsed = JSON.parse(data)
      // dispatch based on parsed.event
    }
  }
}
```

- [ ] **Step 2: Implement chatStore**

Write `app/frontend/src/stores/chatStore.ts` using Zustand:
```ts
import { create } from 'zustand'

interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  thinking?: string
  toolCalls?: string[]
  actionCards?: ActionCardData[]
  suggestedActions?: string[]
  timestamp: Date
}

interface ChatState {
  messages: ChatMessage[]
  isStreaming: boolean
  currentThinking: string
  currentResponse: string
  currentToolCalls: string[]
  addMessage: (msg: ChatMessage) => void
  setStreaming: (val: boolean) => void
  appendThinking: (text: string) => void
  appendResponse: (text: string) => void
  addToolCall: (tool: string) => void
  finishResponse: () => void
  clearHistory: () => void
}
```

- [ ] **Step 3: Type check**

```bash
cd app/frontend && npx tsc --noEmit
```

- [ ] **Step 4: Commit**

```bash
git add app/frontend/src/hooks/useSSE.ts app/frontend/src/stores/chatStore.ts
git commit -m "feat: add useSSE hook with full MAS protocol and Zustand chat store"
```

---

## Task 10: ActionCard Component

**Files:**
- Create: `app/frontend/src/components/vda/ActionCard.tsx`

- [ ] **Step 1: Implement ActionCard**

Write `app/frontend/src/components/vda/ActionCard.tsx` per spec: renders entity card with type icon, title, detail key-value pairs, and action buttons (approve/dismiss). Uses `surface`/`content`/`accent` theme tokens. Framer Motion for enter animation (`initial={{ opacity: 0, y: 10 }}`, `animate={{ opacity: 1, y: 0 }}`).

- [ ] **Step 2: Type check and commit**

```bash
cd app/frontend && npx tsc --noEmit
git add app/frontend/src/components/vda/ActionCard.tsx
git commit -m "feat: add ActionCard component"
```

---

## Task 11: AgentChat Component

**Files:**
- Create: `app/frontend/src/components/vda/AgentChat.tsx`
- Modify: `app/frontend/src/pages/Chat.tsx`

This is the largest component — it ports the entire chat UI from the current `index.html`.

- [ ] **Step 1: Implement AgentChat**

Write `app/frontend/src/components/vda/AgentChat.tsx` per spec. Key sections:

**Welcome state:** Shows `welcomeTitle`, `welcomeSubtitle`, and `suggestedPrompts` as clickable buttons.

**Message list:** Renders `chatStore.messages` as alternating user/assistant bubbles. Assistant messages include:
- Collapsible reasoning block (from `thinking` events) — collapsed by default, click to expand
- Streamed answer text (from `delta` events) — rendered with `react-markdown` + `remark-gfm`
- Tool call step indicators (from `tool_call`/`agent_switch`/`sub_result` events) — vertical step list with spinner for in-progress, check for complete
- Action cards (from `action_card` events) — rendered using `<ActionCard />`
- Suggested follow-ups (from `suggested_actions`) — clickable buttons below the answer

**Input area:** Text input + send button. Disabled while streaming. Auto-focus on mount.

**Session handling:** Catches `session_expired` events and shows a modal prompting re-login.

**MCP approval:** When `autoApproveMcp` is false and an `mcp_approval` event arrives, shows an approval card with tool name/arguments and Approve/Deny buttons.

Uses `useSSE` hook for streaming and `chatStore` for state management.

- [ ] **Step 2: Wire into Chat page**

Update `app/frontend/src/pages/Chat.tsx`:
```tsx
import { AgentChat } from '@/components/vda/AgentChat'

export function Chat() {
  return (
    <AgentChat
      welcomeTitle="Welcome to AI Chat"
      welcomeSubtitle="Ask me anything about your data"
      suggestedPrompts={[
        'Show me a summary of recent activity',
        'What anomalies were detected today?',
      ]}
    />
  )
}
```

- [ ] **Step 3: Type check**

```bash
cd app/frontend && npx tsc --noEmit
```

- [ ] **Step 4: Commit**

```bash
git add app/frontend/src/components/vda/AgentChat.tsx app/frontend/src/pages/Chat.tsx
git commit -m "feat: add AgentChat component with full SSE streaming protocol"
```

---

## Task 12: WorkflowPanel Component

**Files:**
- Create: `app/frontend/src/components/vda/WorkflowPanel.tsx`
- Modify: `app/frontend/src/pages/Workflows.tsx`

- [ ] **Step 1: Implement WorkflowPanel**

Write `app/frontend/src/components/vda/WorkflowPanel.tsx` per spec. Key sections:

**Filter bar:** Severity and status filter dropdowns. Search input.

**Workflow cards:** Grid of cards showing workflow type, severity badge (color-coded), summary, entity reference, timestamp. Click opens detail modal.

**Detail modal:** Uses shadcn Dialog (or build with Radix). Two-column layout:
- Left: workflow details (summary, reasoning chain as expandable JSON, entity reference, timestamps)
- Right: animated agent flow diagram showing the steps the agent took (from `agentSteps` prop)

**Actions:** Approve/dismiss buttons on each card and in the modal. Call PATCH endpoint.

**AI bridge:** "Ask AI" button sends workflow context to chat via `onAskAI` prop.

Uses `useApi` to fetch from endpoint.

- [ ] **Step 2: Wire into Workflows page**

Update `app/frontend/src/pages/Workflows.tsx` to render `<WorkflowPanel />`.

- [ ] **Step 3: Type check and commit**

```bash
cd app/frontend && npx tsc --noEmit
git add app/frontend/src/components/vda/WorkflowPanel.tsx app/frontend/src/pages/Workflows.tsx
git commit -m "feat: add WorkflowPanel component with filters and detail modal"
```

---

## Task 13: KPIDashboard + MetricsBar + ThemeToggle

**Files:**
- Create: `app/frontend/src/components/vda/KPIDashboard.tsx`
- Create: `app/frontend/src/components/vda/MetricsBar.tsx`
- Create: `app/frontend/src/components/vda/ThemeToggle.tsx`

- [ ] **Step 1: Implement KPIDashboard**

Write `KPIDashboard.tsx` per spec: responsive grid of KPI cards. Each card shows icon, label, value, trend arrow (up/down with color), and percent change. Supports 3/4/5 column grid. Loading state shows skeleton shimmer via Tailwind `animate-pulse`. Staggered entrance animation via Framer Motion (`staggerChildren: 0.05`).

- [ ] **Step 2: Implement MetricsBar**

Write `MetricsBar.tsx` per spec: horizontal flex row of compact metric items (icon + label + value). `compact` variant for page headers (smaller text), `full` variant for dashboard rows.

- [ ] **Step 3: Implement ThemeToggle**

Write `ThemeToggle.tsx` per spec: uses `useTheme` hook. `nav` position renders inline sun/moon button. Dropdown (via a simple popover) allows switching between 4 theme presets. Current theme shown with a dot indicator.

- [ ] **Step 4: Type check and commit**

```bash
cd app/frontend && npx tsc --noEmit
git add app/frontend/src/components/vda/KPIDashboard.tsx app/frontend/src/components/vda/MetricsBar.tsx app/frontend/src/components/vda/ThemeToggle.tsx
git commit -m "feat: add KPIDashboard, MetricsBar, and ThemeToggle components"
```

---

## Task 14: DataExplorer Component

**Files:**
- Create: `app/frontend/src/components/vda/DataExplorer.tsx`

- [ ] **Step 1: Implement DataExplorer**

Write `DataExplorer.tsx` per spec: paginated, sortable, filterable table. Key features:
- Column definitions specify type (`text`, `number`, `date`, `badge`, `link`), sortability, filterability
- Badge columns render colored pills based on value
- Sort by clicking column headers (asc/desc toggle)
- Per-column filter dropdowns for filterable columns
- Global search bar (if `searchable` is true)
- Pagination with page size selector and page number buttons
- Row click handler and per-row action buttons
- Loading state shows skeleton rows
- Uses `useApi` to fetch from `endpoint` with query params for page/sort/filter

Built on native HTML `<table>` with Tailwind styling (matching the spec's design system), NOT a third-party table library.

- [ ] **Step 2: Type check and commit**

```bash
cd app/frontend && npx tsc --noEmit
git add app/frontend/src/components/vda/DataExplorer.tsx
git commit -m "feat: add DataExplorer component with sort, filter, and pagination"
```

---

## Task 15: TimelineView + ExceptionManager

**Files:**
- Create: `app/frontend/src/components/vda/TimelineView.tsx`
- Create: `app/frontend/src/components/vda/ExceptionManager.tsx`

- [ ] **Step 1: Implement TimelineView**

Write `TimelineView.tsx` per spec: vertical timeline with type-colored icons. Events grouped by `day` or `hour`. Each event shows timestamp, title, description, severity badge. Click handler on events. Respects `maxItems` limit with a "show more" link.

- [ ] **Step 2: Implement ExceptionManager**

Write `ExceptionManager.tsx` per spec: list of exception cards with severity color-coding, inline action buttons (acknowledge/escalate/resolve/dismiss), and an "Ask AI" button that bridges to chat. Uses `useApi` to fetch from endpoint.

- [ ] **Step 3: Type check and commit**

```bash
cd app/frontend && npx tsc --noEmit
git add app/frontend/src/components/vda/TimelineView.tsx app/frontend/src/components/vda/ExceptionManager.tsx
git commit -m "feat: add TimelineView and ExceptionManager components"
```

---

## Task 16: NotesPanel + LiveFeedIndicator

**Files:**
- Create: `app/frontend/src/components/vda/NotesPanel.tsx`
- Create: `app/frontend/src/components/vda/LiveFeedIndicator.tsx`
- Create: `app/frontend/src/hooks/useLiveFeed.ts`

- [ ] **Step 1: Implement NotesPanel**

Write `NotesPanel.tsx` per spec: slide-out panel (right side) with a list of notes and a form to add new ones. Fetches from `/api/notes?entity_type=X&entity_id=Y`. Each note shows text, author, and relative timestamp. New note form at the bottom with a textarea and submit button.

- [ ] **Step 2: Implement useLiveFeed hook**

Write `app/frontend/src/hooks/useLiveFeed.ts`:
```ts
import { useApi } from './useApi'

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

  const start = async () => { /* POST /api/streaming/start-live-feed */ }
  const stop = async () => { /* POST /api/streaming/stop-live-feed */ }

  return { status: data, loading, error, start, stop, refetch }
}
```

- [ ] **Step 3: Implement LiveFeedIndicator**

Write `LiveFeedIndicator.tsx` per spec: pulsing green dot when running, stats display, optional start/stop toggle. Uses `useLiveFeed` hook.

- [ ] **Step 4: Type check and commit**

```bash
cd app/frontend && npx tsc --noEmit
git add app/frontend/src/components/vda/NotesPanel.tsx app/frontend/src/components/vda/LiveFeedIndicator.tsx app/frontend/src/hooks/useLiveFeed.ts
git commit -m "feat: add NotesPanel, LiveFeedIndicator, and useLiveFeed hook"
```

---

## Task 17: GeoView Component

**Files:**
- Create: `app/frontend/src/components/vda/GeoView.tsx`

- [ ] **Step 1: Install Leaflet**

```bash
cd app/frontend && npm install leaflet react-leaflet && npm install -D @types/leaflet
```

- [ ] **Step 2: Implement GeoView**

Write `GeoView.tsx` per spec: wraps react-leaflet's `MapContainer` (renamed to avoid collision). Renders markers, animated route lines, and optional heatmap layer. Handles the tab-switch invalidation issue (gotcha #50) by calling `map.invalidateSize()` via a `useEffect` on visibility.

Key implementation:
- Use `useMap()` inside a child component to access the map instance
- On visibility change (IntersectionObserver or parent tab switch), call `invalidateSize()`
- Markers use custom icons based on `color` prop
- Route lines use `Polyline` with `dashArray` animation for animated routes

- [ ] **Step 3: Type check and commit**

```bash
cd app/frontend && npx tsc --noEmit
git add app/frontend/src/components/vda/GeoView.tsx app/frontend/package.json app/frontend/package-lock.json
git commit -m "feat: add GeoView component with Leaflet, markers, routes, and tab-switch fix"
```

---

## Task 18: shadcn/ui Primitives

**Files:**
- Create: `app/frontend/src/components/ui/button.tsx`
- Create: `app/frontend/src/components/ui/card.tsx`
- Create: `app/frontend/src/components/ui/dialog.tsx`
- Create: `app/frontend/src/components/ui/badge.tsx`
- Create: `app/frontend/src/components/ui/input.tsx`
- Create: `app/frontend/src/components/ui/skeleton.tsx`
- Create: `app/frontend/src/components/ui/dropdown-menu.tsx`
- Create: `app/frontend/src/components/ui/sheet.tsx`
- Create: `app/frontend/src/components/ui/tooltip.tsx`

- [ ] **Step 1: Install shadcn/ui Radix dependencies**

```bash
cd app/frontend && npm install @radix-ui/react-dialog @radix-ui/react-dropdown-menu @radix-ui/react-tooltip @radix-ui/react-slot class-variance-authority
```

- [ ] **Step 2: Add shadcn/ui primitive components**

Create each component in `app/frontend/src/components/ui/` following standard shadcn/ui patterns. These are the primitives used by the VDA compound components. Use the `cn()` utility from `lib/utils.ts`. Style with VDA theme tokens (`surface`, `content`, `accent`).

Components needed: Button, Card (CardHeader, CardContent, CardFooter), Dialog (DialogContent, DialogHeader, DialogTitle, DialogDescription), Badge, Input, Skeleton, DropdownMenu, Sheet (slide-out panel), Tooltip.

- [ ] **Step 3: Type check and commit**

```bash
cd app/frontend && npx tsc --noEmit
git add app/frontend/src/components/ui/
git commit -m "feat: add shadcn/ui primitive components styled with VDA theme tokens"
```

**Note:** This task should be done early (before the compound components that depend on them). In practice, the implementing agent should do this task before Tasks 10-17. The plan lists it here for logical grouping but the `subagent-driven-development` skill should reorder if needed.

---

## Task 19: Integration Verification

**Files:**
- Modify: `app/frontend/src/App.tsx` (wire ThemeToggle into header)
- Modify: `app/frontend/src/pages/Dashboard.tsx` (add sample KPIDashboard)

- [ ] **Step 1: Wire ThemeToggle into AppShell header**

Update `App.tsx` to pass `<ThemeToggle position="nav" />` as the `headerRight` prop to `<AppShell>`.

- [ ] **Step 2: Add sample content to Dashboard**

Update `Dashboard.tsx` to render a `<KPIDashboard>` with static sample metrics and a `<DataExplorer>` with static sample data. This verifies components render correctly without a backend.

- [ ] **Step 3: Full type check**

```bash
cd app/frontend && npx tsc --noEmit
```
Expected: zero errors across all files.

- [ ] **Step 4: Full build**

```bash
cd app/frontend && npm run build
```
Expected: clean production build to `dist/`. No warnings.

- [ ] **Step 5: Verify build serves from FastAPI**

```bash
cd app && python -c "
import os
from backend.main import app
d = os.path.join(os.path.dirname(os.path.abspath('backend/main.py')), 'frontend', 'dist')
print('dist exists:', os.path.isdir(d))
print('index.html exists:', os.path.isfile(os.path.join(d, 'index.html')))
"
```

- [ ] **Step 6: Commit**

```bash
git add app/frontend/src/App.tsx app/frontend/src/pages/Dashboard.tsx
git commit -m "feat: wire ThemeToggle into AppShell and add sample dashboard content"
```

---

## Task 20: Remove Old Frontend + Final Verification

**Files:**
- Delete: `app/frontend/src/index.html` (the 157KB monolith)
- Modify: `app/frontend/.gitignore` (add `dist/` and `node_modules/`)

- [ ] **Step 1: Create .gitignore**

Write `app/frontend/.gitignore`:
```
node_modules/
dist/
```

- [ ] **Step 2: Remove old frontend**

```bash
rm app/frontend/src/index.html
```

- [ ] **Step 3: Final type check + build**

```bash
cd app/frontend && npx tsc --noEmit && npm run build
```
Expected: zero errors, clean build.

- [ ] **Step 4: Verify file count**

```bash
find app/frontend/src -name '*.tsx' -o -name '*.ts' -o -name '*.css' | wc -l
```
Expected: ~35-40 files (12 VDA components + 4 hooks + 3 layouts + 3 pages + types + lib + stores + config + styles).

- [ ] **Step 5: Commit**

```bash
git add -A app/frontend/
git rm app/frontend/src/index.html 2>/dev/null || true
git commit -m "feat: complete React frontend migration — remove old single-HTML frontend

Replaces the 157KB monolith index.html with a React + Vite app featuring:
- 12 VDA compound components on shadcn/ui primitives
- 4 industry themes with light/dark mode
- 3 composable layouts (sidebar, topnav, dashboard)
- Route-based navigation with lazy loading
- useSSE hook with full MAS streaming protocol
- useApi hook with loading/error/polling
- Zustand chat store
- Extracted backend routes (chat, workflows)"
```

---

## Execution Order Note

The tasks are numbered for reference but some have implicit dependencies:

1. **Task 18 (shadcn/ui primitives) should be done before Tasks 10-17** — the VDA compound components depend on Button, Card, Dialog, Badge, etc.
2. **Tasks 1-7** are strictly sequential (each builds on the previous).
3. **Task 8 (backend extraction)** is independent of frontend tasks and can run in parallel.
4. **Tasks 10-17 (components)** can run in parallel after Tasks 3, 4, 5, 9, and 18 are complete.
5. **Tasks 19-20** must be last.

Recommended execution order:
```
Task 1 → Task 2 → Task 3 → Task 4 → Task 5 → Task 18 (shadcn primitives)
                                                  ↓
Task 8 (backend, parallel) ────────────────→ Task 6 → Task 7 → Task 9
                                                  ↓
                                    Tasks 10-17 (components, parallelizable)
                                                  ↓
                                         Task 19 → Task 20
```
