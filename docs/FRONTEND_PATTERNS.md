# Frontend Patterns Reference

SSE streaming protocol, action cards, CSS theming, and page creation patterns. Referenced from CLAUDE.md.

---

## SSE Streaming Protocol

The chat UI handles these SSE event types (all implemented in `sendChat()`):

| Event | Purpose | UI Action |
|-------|---------|-----------|
| `delta` | Text chunk from the final answer | Stream into the answer div |
| `tool_call` | Sub-agent invoked | Show as step indicator |
| `agent_switch` | MAS switched sub-agents | Update step |
| `sub_result` | Data returned from sub-agent | Show as completed step |
| `action_card` | Entity created/referenced | Render interactive card |
| `suggested_actions` | Follow-up prompts | Render as clickable buttons |
| `error` | Error message | Display in red |
| `[DONE]` | Stream complete | Finalize UI |

## Action Cards

Configure `ACTION_CARD_TABLES` in `main.py` to auto-detect entities created during chat:

```python
ACTION_CARD_TABLES = [
    {
        "table": "purchase_orders",
        "card_type": "purchase_order",
        "id_col": "po_id",
        "display_fields": ["po_number", "supplier", "total_amount", "status"],
    },
    {
        "table": "work_orders",
        "card_type": "work_order",
        "id_col": "wo_id",
        "display_fields": ["wo_number", "asset_name", "priority", "status"],
    },
]
```

Each card gets approve/dismiss buttons that PATCH the entity status via your API.

## CSS Variables for Theming

Override these in `:root` to rebrand. Variables use semantic names, not color names:

```css
:root {
  --primary: #1a2332;     /* Main dark — sidebar, headers */
  --accent: #f59e0b;      /* CTA / highlight color */
  --green: #10b981;       /* Success */
  --red: #ef4444;         /* Error/critical */
  --blue: #3b82f6;        /* Info */
}
```

**Theme presets:**
- Dark industrial (navy/orange): `--primary: #1a2332; --accent: #f59e0b;`
- Clean medical (white/teal): `--primary: #f8fafc; --accent: #14b8a6;`
- Corporate blue (navy/blue): `--primary: #1e3a5f; --accent: #3b82f6;`

## Adding New Pages

1. Add nav link in sidebar: `<a href="#" data-page="mypage">...</a>`
2. Add page div: `<div id="page-mypage" class="page">...</div>`
3. Add to `PAGES` array and `PAGE_TITLES` map in JS
4. Add `loadMypage()` function and call it from `navigate()`
5. Use `fetchApi()` to load data and render into the page div

## formatAgentName() Mapping

Customize this function to map MAS tool names to display labels:

```javascript
function formatAgentName(name) {
  const shortName = name.includes('__') ? name.split('__').pop() : name;
  const map = {
    'my_data_space': 'Data Query',
    'my_knowledge_base': 'Knowledge Base',
    'my_calculator': 'Calculator Tool',
    'mcp-lakebase-connection': 'Database (write)',
  };
  return map[shortName] || map[name] || shortName.replace(/[-_]/g, ' ');
}
```

## CSS Component Toolkit

These classes are available in the template and layout-agnostic:

| Class | Purpose |
|-------|---------|
| `.kpi-row` | Horizontal row of KPI cards |
| `.card` | Container with shadow and border-radius |
| `.grid-2`, `.grid-3` | CSS grid with 2 or 3 columns |
| `.badge-*` | Status badges (success, warning, error, info) |
| `.btn-*` | Button variants (primary, secondary, danger) |
| `.filter-bar` | Horizontal filter controls |
| `table` | Styled data table |
| `.pill-*` | Small pill badges |

## JS Utility Functions

| Function | Purpose |
|----------|---------|
| `fetchApi(path)` | GET from `/api/...` with error handling |
| `postApi(path, body)` | POST JSON to `/api/...` |
| `patchApi(path, body)` | PATCH JSON to `/api/...` |
| `showSkeleton(el)` | Show loading skeleton in element |
| `animateKPIs()` | Animate KPI number entrance |
| `askAI(prompt)` | Navigate to chat page with pre-filled prompt |
| `fmt(n)` | Format number with commas |
| `navigate(page)` | Navigate to a page by name |
| `escHtml(str)` | Escape HTML entities |
| `formatMd(str)` | Convert markdown to HTML |

## Frontend Generation Flow

**IMPORTANT: Before building any frontend pages, ask the user these questions:**

1. **Layout style** — Sidebar nav (default), top nav bar, or dashboard-first?
2. **Color scheme** — Dark industrial (navy/orange), clean medical (white/teal), corporate blue (navy/blue), or custom hex?
3. **Dashboard content** — KPI cards, charts, tables, morning briefing, command-center with AI input?
4. **Additional pages** — Beyond AI Chat and Agent Workflows (included), what domain pages?

**Included starter pages (functional — customize, don't rebuild):**
- **AI Chat** — Full SSE streaming with sub-agent steps, action cards, follow-ups. Customize: suggested prompts, welcome card text, `formatAgentName()`.
- **Agent Workflows** — Workflow cards with severity, status filters, centered modal. Customize: `DOMAIN_AGENTS`, `WORKFLOW_AGENTS`, `TYPE_LABELS`.

**The template layout (sidebar + topbar) is a minimal placeholder.** Replace it entirely based on the user's layout preference.

## Streaming UI Patterns

When `streaming.enabled: true`, the template includes optional streaming components wrapped in `<!-- STREAMING: START -->` / `<!-- STREAMING: END -->` comment blocks.

### Telemetry Status Bar

A fixed/sticky bar showing live feed status, KPI tiles, and a Start/Stop toggle:

```html
<div id="telemetry-bar" class="zb-bar">
    <div class="zb-status">
        <span class="zb-pulse"></span>
        <span id="feed-status-text">Live Feed: Off</span>
    </div>
    <div class="zb-kpis">
        <div class="zb-kpi">
            <span id="kpi-stream1" class="zb-kpi-value">--</span>
            <span class="zb-kpi-label">Stream 1</span>
        </div>
        <!-- Add more KPI tiles per stream -->
    </div>
    <button id="feed-toggle-btn" class="zb-toggle" onclick="toggleLiveFeed()">
        Start Live Feed
    </button>
</div>
```

**Customization:** Replace "Stream 1", "Stream 2" labels with domain-specific names (e.g., "GPS Pings", "Sensor Readings"). Map `loadTelemetryStats()` response fields to the correct KPI tile IDs.

### Live Feed Toggle Pattern

```javascript
async function toggleLiveFeed() {
    const btn = document.getElementById('feed-toggle-btn');
    if (!liveFeedActive) {
        // Start: POST /api/streaming/start-live-feed
        // Update button to "Stop", add .active class, start polling stats
        telemetryInterval = setInterval(loadTelemetryStats, 15000);
    } else {
        // Stop: POST /api/streaming/stop-live-feed
        // Update button to "Start", remove .active class, clear interval
        clearInterval(telemetryInterval);
    }
}
```

**Key behavior:** When the feed starts, `loadTelemetryStats()` polls `/api/streaming/stats` every 15 seconds to update KPI tiles. When the feed stops (manually or auto-timeout), polling stops.

### Auto-Refresh Interval Management

Start polling when the streaming page is visible, stop when navigating away:

```javascript
// In navigate() function:
function navigate(page) {
    // ... existing page switch logic ...

    // Start/stop streaming refresh based on page visibility
    if (page === 'streaming' || page === 'dashboard') {
        if (liveFeedActive && !telemetryInterval) {
            telemetryInterval = setInterval(loadTelemetryStats, 15000);
        }
    } else {
        if (telemetryInterval) {
            clearInterval(telemetryInterval);
            telemetryInterval = null;
        }
    }
}
```

### Feed Status Recovery

On page load, check if a feed is already running (handles app restart or page refresh):

```javascript
// Call on page load:
async function checkFeedStatus() {
    const resp = await fetchApi('/api/streaming/live-feed-status');
    if (resp.running && !liveFeedActive) {
        liveFeedActive = true;
        // Update UI to reflect active state
        // Start polling interval
    }
}
checkFeedStatus();
```

### CSS for Streaming Components

```css
.zb-bar {
    display: flex; align-items: center; gap: 24px;
    padding: 12px 24px; background: var(--card-bg);
    border-bottom: 1px solid var(--border);
}
.zb-pulse {
    width: 8px; height: 8px; border-radius: 50%;
    background: var(--text-muted); display: inline-block;
}
.zb-pulse.live {
    background: var(--green);
    animation: pulse 1.5s ease-in-out infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.5; transform: scale(1.3); }
}
.zb-kpi { text-align: center; }
.zb-kpi-value { font-size: 1.5rem; font-weight: 700; display: block; }
.zb-kpi-label { font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; }
.zb-toggle {
    padding: 8px 20px; border: none; border-radius: 6px; cursor: pointer;
    font-weight: 600; background: var(--green); color: #fff;
}
.zb-toggle.active { background: var(--red); }
.zb-toggle:disabled { opacity: 0.5; cursor: not-allowed; }
```
