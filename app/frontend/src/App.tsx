import { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { LayoutDashboard, MessageSquare, GitBranch } from 'lucide-react'
import { AppShell } from '@/layouts/AppShell'
import { ThemeToggle } from '@/components/vda/ThemeToggle'
import { demoConfig } from '@/demo-config'
import type { RouteConfig } from '@/types'

const Dashboard = lazy(() => import('./pages/Dashboard').then(m => ({ default: m.Dashboard })))
const Chat = lazy(() => import('./pages/Chat').then(m => ({ default: m.Chat })))
const Workflows = lazy(() => import('./pages/Workflows').then(m => ({ default: m.Workflows })))

export const routes: RouteConfig[] = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard, page: Dashboard },
  { path: '/chat', label: 'AI Chat', icon: MessageSquare, page: Chat },
  { path: '/workflows', label: 'Workflows', icon: GitBranch, page: Workflows },
]

export function App() {
  return (
    <BrowserRouter>
      <AppShell
        layout={demoConfig.layout}
        demoName={demoConfig.name}
        routes={routes}
        headerRight={<ThemeToggle position="nav" />}
      >
        <Suspense fallback={<div className="animate-pulse bg-surface-hover h-64 rounded-lg" />}>
          <Routes>
            {routes.map((route) => (
              <Route key={route.path} path={route.path} element={<route.page />} />
            ))}
          </Routes>
        </Suspense>
      </AppShell>
    </BrowserRouter>
  )
}
