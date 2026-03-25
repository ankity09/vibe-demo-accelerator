import { useLocation, Link } from 'react-router-dom'
import { cn } from '@/lib/utils'
import type { RouteConfig } from '@/types'

interface TopNavLayoutProps {
  demoName: string
  routes: RouteConfig[]
  logo?: React.ReactNode
  headerRight?: React.ReactNode
  children: React.ReactNode
}

export function TopNavLayout({
  demoName,
  routes,
  logo,
  headerRight,
  children,
}: TopNavLayoutProps) {
  const location = useLocation()

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-surface-primary">
      {/* Top Nav Bar */}
      <header className="flex items-center bg-surface-primary border-b border-border h-14 flex-shrink-0 px-6">
        {/* Left: Logo + Name */}
        <div className="flex items-center gap-3 mr-8 flex-shrink-0">
          {logo && (
            <div className="w-7 h-7 flex items-center justify-center">
              {logo}
            </div>
          )}
          <span className="text-content-primary font-semibold text-sm">
            {demoName}
          </span>
        </div>

        {/* Center: Nav Links */}
        <nav className="flex items-center gap-1 flex-1">
          {routes.map((route) => {
            const isActive = location.pathname === route.path
            const Icon = route.icon
            return (
              <Link
                key={route.path}
                to={route.path}
                className={cn(
                  'flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium',
                  'transition-colors duration-150 relative',
                  isActive
                    ? 'text-accent after:absolute after:bottom-[-10px] after:left-0 after:right-0 after:h-[2px] after:bg-accent after:rounded-full'
                    : 'text-content-secondary hover:text-content-primary hover:bg-surface-hover'
                )}
              >
                <Icon className="w-4 h-4 flex-shrink-0" />
                <span>{route.label}</span>
              </Link>
            )
          })}
        </nav>

        {/* Right: Slot */}
        {headerRight && (
          <div className="flex items-center gap-2 flex-shrink-0 ml-4">
            {headerRight}
          </div>
        )}
      </header>

      {/* Content */}
      <main className="flex-1 overflow-auto p-6">{children}</main>
    </div>
  )
}
