import { useState } from 'react'
import { useLocation, Link } from 'react-router-dom'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { RouteConfig } from '@/types'

interface SidebarLayoutProps {
  demoName: string
  routes: RouteConfig[]
  logo?: React.ReactNode
  headerRight?: React.ReactNode
  children: React.ReactNode
}

export function SidebarLayout({
  demoName,
  routes,
  logo,
  headerRight,
  children,
}: SidebarLayoutProps) {
  const [collapsed, setCollapsed] = useState(false)
  const location = useLocation()

  return (
    <div className="flex h-screen overflow-hidden bg-surface-primary">
      {/* Sidebar */}
      <aside
        className={cn(
          'flex flex-col bg-surface-primary border-r border-border flex-shrink-0',
          'transition-all duration-200',
          collapsed ? 'w-16' : 'w-[280px]'
        )}
      >
        {/* Logo + Demo Name */}
        <div
          className={cn(
            'flex items-center gap-3 px-4 py-5 border-b border-border',
            collapsed && 'justify-center px-0'
          )}
        >
          {logo && (
            <div className="flex-shrink-0 w-8 h-8 flex items-center justify-center">
              {logo}
            </div>
          )}
          {!collapsed && (
            <span className="text-content-primary font-semibold text-sm leading-tight truncate">
              {demoName}
            </span>
          )}
        </div>

        {/* Nav Links */}
        <nav className="flex-1 overflow-y-auto py-4 space-y-1 px-2">
          {routes.map((route) => {
            const isActive = location.pathname === route.path
            const Icon = route.icon
            return (
              <Link
                key={route.path}
                to={route.path}
                title={collapsed ? route.label : undefined}
                className={cn(
                  'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium',
                  'transition-colors duration-150',
                  isActive
                    ? 'bg-accent/10 text-accent'
                    : 'text-content-secondary hover:bg-surface-hover hover:text-content-primary',
                  collapsed && 'justify-center px-0'
                )}
              >
                <Icon className="w-4 h-4 flex-shrink-0" />
                {!collapsed && (
                  <span className="truncate">{route.label}</span>
                )}
              </Link>
            )
          })}
        </nav>

        {/* Collapse Toggle */}
        <div className="border-t border-border p-2">
          <button
            onClick={() => setCollapsed((c) => !c)}
            className={cn(
              'w-full flex items-center justify-center rounded-md p-2',
              'text-content-muted hover:text-content-primary hover:bg-surface-hover',
              'transition-colors duration-150'
            )}
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {collapsed ? (
              <ChevronRight className="w-4 h-4" />
            ) : (
              <ChevronLeft className="w-4 h-4" />
            )}
          </button>
        </div>
      </aside>

      {/* Main area */}
      <div className="flex flex-col flex-1 min-w-0">
        {/* Header */}
        <header className="flex items-center justify-between px-6 bg-surface-secondary border-b border-border h-14 flex-shrink-0">
          <span className="text-content-primary font-semibold text-sm truncate">
            {demoName}
          </span>
          {headerRight && (
            <div className="flex items-center gap-2 flex-shrink-0 ml-4">
              {headerRight}
            </div>
          )}
        </header>

        {/* Content */}
        <main className="flex-1 overflow-auto p-6">{children}</main>
      </div>
    </div>
  )
}
