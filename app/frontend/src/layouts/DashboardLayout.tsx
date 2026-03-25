import { useState } from 'react'
import { useLocation, Link } from 'react-router-dom'
import { Menu, X } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { RouteConfig } from '@/types'

interface DashboardLayoutProps {
  demoName: string
  routes: RouteConfig[]
  logo?: React.ReactNode
  headerRight?: React.ReactNode
  children: React.ReactNode
}

export function DashboardLayout({
  demoName,
  routes,
  logo,
  headerRight: _headerRight,
  children,
}: DashboardLayoutProps) {
  const [drawerOpen, setDrawerOpen] = useState(false)
  const location = useLocation()

  return (
    <div className="relative h-screen overflow-hidden bg-surface-primary">
      {/* Floating Hamburger Button */}
      <button
        onClick={() => setDrawerOpen(true)}
        className={cn(
          'fixed top-4 left-4 z-50 p-2 rounded-lg',
          'bg-surface-card shadow-lg border border-border',
          'text-content-secondary hover:text-content-primary hover:bg-surface-hover',
          'transition-colors duration-150'
        )}
        aria-label="Open navigation"
      >
        <Menu className="w-5 h-5" />
      </button>

      {/* Drawer Overlay */}
      {drawerOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50"
          onClick={() => setDrawerOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Slide-out Drawer */}
      <aside
        className={cn(
          'fixed top-0 left-0 z-50 h-full w-64 bg-surface-primary border-r border-border',
          'flex flex-col',
          'transition-transform duration-200',
          drawerOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        {/* Drawer Header */}
        <div className="flex items-center justify-between px-4 py-5 border-b border-border">
          <div className="flex items-center gap-3">
            {logo && (
              <div className="w-7 h-7 flex items-center justify-center">
                {logo}
              </div>
            )}
            <span className="text-content-primary font-semibold text-sm leading-tight truncate">
              {demoName}
            </span>
          </div>
          <button
            onClick={() => setDrawerOpen(false)}
            className={cn(
              'p-1 rounded-md flex-shrink-0',
              'text-content-muted hover:text-content-primary hover:bg-surface-hover',
              'transition-colors duration-150'
            )}
            aria-label="Close navigation"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Drawer Nav Links */}
        <nav className="flex-1 overflow-y-auto py-4 space-y-1 px-2">
          {routes.map((route) => {
            const isActive = location.pathname === route.path
            const Icon = route.icon
            return (
              <Link
                key={route.path}
                to={route.path}
                onClick={() => setDrawerOpen(false)}
                className={cn(
                  'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium',
                  'transition-colors duration-150',
                  isActive
                    ? 'bg-accent/10 text-accent'
                    : 'text-content-secondary hover:bg-surface-hover hover:text-content-primary'
                )}
              >
                <Icon className="w-4 h-4 flex-shrink-0" />
                <span className="truncate">{route.label}</span>
              </Link>
            )
          })}
        </nav>
      </aside>

      {/* Full-screen Content */}
      <main className="h-full overflow-auto p-6">{children}</main>
    </div>
  )
}
